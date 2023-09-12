import sys
from datetime import datetime
from pathlib import Path
from typing import List, cast

import PySimpleGUI as sg
import dotenv
from despatchbay.despatchbay_entities import CollectionDate, Service, ShipmentRequest
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from ..core.cmc_updater import PS_FUNCS, edit_commence
from ..core.config import Config, logger
from ..core.desp_client_wrapper import APIClientWrapper
from ..core.enums import Contact, DateTimeMasks, DbayCreds, ShipmentCategory
from ..core.funcs import collection_date_to_datetime, email_label, print_label
from ..gui import keys_and_strings
from ..gui.main_gui import main_window, post_book
from .addresser import get_home_sender_recip, get_remote_recipient, remote_address_script, \
    sender_from_contact_address
from .edit_shipment import address_click, boxes_click, date_click, dropoff_click, get_parcels, service_click
from .shipment import ShipmentAddressed, ShipmentBooked, ShipmentCmcUpdated, ShipmentForRequest, \
    ShipmentGuiConfirmed, ShipmentInput, \
    ShipmentPrepared, ShipmentCompleted, ShipmentQueued, ShipmentRequested, records_from_dbase, shipments_from_records
from .tracker import get_tracking

dotenv.load_dotenv()
DESP_CLIENT: DespatchBaySDK | None = None


class Shipper:
    """ Utility class to hold config and DespatchBay client"""

    def __init__(self, dbay_creds: DbayCreds):
        global DESP_CLIENT
        try:
            # client = DespatchBaySDK(api_user=dbay_creds.api_user, api_key=dbay_creds.api_key)
            client = DespatchBaySDK(**dbay_creds.__dict__)
        except Exception as e:
            logger.exception(e)
            raise ApiException("Unable to intitialise DespatchBay client")
        client = APIClientWrapper(client)
        client = cast(DespatchBaySDK, client)
        DESP_CLIENT = client


def dispatch(config: Config, shipments: List[ShipmentInput]):
    """ Shipment processing pipeline - takes list of ShipmentInput and Config objects,
    walks through addressing and preparation steps before selectively booking collecitons and printing labels as per GUI"""
    shipments_addressed = [address_shipment(shipment=shipment, home_address=config.home_address,
                                            home_contact=config.home_contact) for shipment in shipments]
    shipments_prepared = [prepare_shipment(shipment=shipment, default_shipping_service=config.default_shipping_service)
                          for shipment in shipments_addressed]
    shipments_for_request = [pre_request_shipment(default_shipping_service=config.default_shipping_service,
                                                  shipment=shipment) for shipment in shipments_prepared]
    shipments_requested = [request_shipment(shipment=shipment) for shipment in shipments_for_request]
    shipments_complete = dispatch_loop(config=config, shipments=shipments_requested)
    post_book(shipments=shipments_complete)

    # if not booked_shipments:
    #     logger.warning('No shipments, exiting')
    #     sys.exit()


def get_shipments(outbound: bool, import_mappings: dict, category: ShipmentCategory,
                  dbase_file: Path) -> List[ShipmentInput]:
    """ returns a list of validated shipments from a dbase file and a mapping dict"""

    logger.info(f'DBase file og = {dbase_file}')
    import_map_name = f"{category.name.lower()}_mapping"
    import_map = import_mappings[import_map_name]
    logger.info(f'Import map = {import_map_name} - {import_map}')

    records = records_from_dbase(dbase_file)
    shipments = shipments_from_records(category=category, import_map=import_map, outbound=outbound,
                                       records=records)
    return shipments


def address_shipment(shipment: ShipmentInput, home_address, home_contact) -> ShipmentAddressed:
    """ gets Contact, Address, Sender and Recipient objects"""
    remote_contact = Contact(name=shipment.contact_name, email=shipment.email, telephone=shipment.telephone)
    remote_address = remote_address_script(shipment=shipment, remote_contact=remote_contact)
    if shipment.is_outbound:
        sender = get_home_sender_recip(home_contact=home_contact, home_address=home_address,
                                       outbound=shipment.is_outbound)
        recipient = get_remote_recipient(contact=remote_contact,
                                         remote_address=remote_address)
    else:
        sender = sender_from_contact_address(contact=remote_contact,
                                             remote_address=remote_address)
        recipient = get_home_sender_recip(home_contact=home_contact, home_address=home_address,
                                          outbound=shipment.is_outbound)
    return ShipmentAddressed(**shipment.__dict__, remote_contact=remote_contact, sender=sender, recipient=recipient,
                             remote_address=remote_address)


def prepare_shipment(shipment: ShipmentAddressed, default_shipping_service) -> ShipmentPrepared:
    """ Gets objects for all available CollectionDates and Services, creates menu maps for gui"""
    available_dates = DESP_CLIENT.get_available_collection_dates(sender_address=shipment.sender,
                                                                 courier_id=default_shipping_service.courier)
    all_services = DESP_CLIENT.get_services()
    date_menu_map = keys_and_strings.DATE_MENU(available_dates)
    service_menu_map = keys_and_strings.SERVICE_MENU(all_services)

    return ShipmentPrepared(**shipment.__dict__, available_dates=available_dates, all_services=all_services,
                            date_menu_map=date_menu_map, service_menu_map=service_menu_map)


def pre_request_shipment(shipment: ShipmentPrepared, default_shipping_service) -> ShipmentForRequest:
    """ gets actual CollectionDate, Service and Parcel objects"""
    shipment.parcels = get_parcels(num_parcels=shipment.boxes)
    service_id = default_shipping_service.service
    shipment.collection_date = get_collection_date(shipment=shipment, available_dates=shipment.available_dates)

    # need a shipment_request to get a service, need a service to get a shipment_request.... (thanks dbay)
    # so make a temp request to get all services, then get the actually available services from that
    temp_request = DESP_CLIENT.shipment_request(
        service_id=service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer_printable,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )

    available_services = DESP_CLIENT.get_available_services(temp_request)
    shipment.service = get_actual_service(default_service_id=default_shipping_service.service,
                                          available_services=available_services, shipment=shipment)

    return ShipmentForRequest(**shipment.__dict__, **shipment.model_extra)


def request_shipment(shipment: ShipmentForRequest) -> ShipmentRequested:
    """ gets shipment request"""
    shipment.shipment_request = get_shipment_request(shipment=shipment)
    return ShipmentRequested(**shipment.__dict__ | shipment.model_extra)


def gui_confirm_shipment(shipment: ShipmentRequested, values: dict) -> ShipmentGuiConfirmed:
    """ reads gui checkboxes"""
    read_window_cboxs(values=values, shipment=shipment)
    return ShipmentGuiConfirmed(**shipment.__dict__, **shipment.model_extra)


def process_shipment(shipment_req: ShipmentRequested, values: dict, config: Config) -> ShipmentBooked | ShipmentQueued:
    """ queues and books shipment, updates commence, prints and emails label"""
    if not sg.popup_yes_no("Queue and book shipments?") == 'Yes':
        if sg.popup_ok_cancel("Ok to quit, cancel to continue booking") == 'OK':
            logger.info('User quit')
            sys.exit()

    shipment: ShipmentGuiConfirmed = gui_confirm_shipment(shipment=shipment_req, values=values)
    shipment: ShipmentQueued = queue_shipment(shipment=shipment)
    shipment: ShipmentCmcUpdated = maybe_update_commence(config=config, shipment=shipment)
    if not shipment.is_to_book:
        return shipment

    shipment:ShipmentBooked = book_shipment(shipment=shipment)

    shipment.label_location = download_shipment_label(shipment=shipment, config=config)

    print_email_label(print_email=shipment.is_to_print_email, email_body=config.return_label_email_body,
                      shipment=shipment)

    booked = ShipmentCompleted(**shipment.__dict__, **shipment.model_extra)

    return booked


def dispatch_loop(config: Config, shipments: List[ShipmentRequested]) -> List[ShipmentBooked | ShipmentQueued]:
    """ pysimplegui main_loop, takes list of ShipmentRequested objects
    listens for user input to edit and update shipments
    listens for go_ship  button to start booking collection etc"""
    logger.info('GUI LOOP')

    if config.sandbox:
        sg.theme('Tan')
    else:
        sg.theme('Dark Blue')

    window = main_window(shipments=shipments, outbound=config.outbound)
    processed_shipments = []

    while True:
        package = None
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            window.close()
            sys.exit()

        if event == keys_and_strings.GO_SHIP_KEY():
            # if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
            #     sg.popup_quick_message('Please Wait')
            window.close()

            for shipment in shipments:
                # if not compare_before_send(shipment=shipment):
                #     pass
                sg.popup_quick_message('Processing shipments, please wait...')
                processed = process_shipment(shipment_req=shipment, values=values, config=config)
                if processed is not None:
                    processed_shipments.append(processed)
                else:
                    continue
            return processed_shipments

        # todo if values[event] == shipment_to_edit ie make .eq() in shipmentinput
        shipment_to_edit: ShipmentRequested = next((shipment for shipment in shipments if
                                                    keys_and_strings.SHIPMENT_KEY(shipment) in event.upper()))

        if event == keys_and_strings.BOXES_KEY(shipment_to_edit):
            package = boxes_click(shipment_to_edit=shipment_to_edit, window=window)

        elif event == keys_and_strings.SERVICE_KEY(shipment_to_edit):
            package = service_click(shipment_to_edit=shipment_to_edit, location=window.mouse_location())

        elif event == keys_and_strings.DATE_KEY(shipment_to_edit):
            package = date_click(location=window.mouse_location(), shipment_to_edit=shipment_to_edit)

        elif event == keys_and_strings.SENDER_KEY(shipment_to_edit):
            package = address_click(shipment=shipment_to_edit, target=shipment_to_edit.sender)

        elif event == keys_and_strings.RECIPIENT_KEY(shipment_to_edit):
            package = address_click(shipment=shipment_to_edit, target=shipment_to_edit.recipient)

        elif event == keys_and_strings.REMOVE_KEY(shipment_to_edit):
            shipments = [s for s in shipments if s != shipment_to_edit]
            window.close()
            window = main_window(shipments=shipments, outbound=config.outbound)

        elif event == keys_and_strings.CUSTOMER_KEY(shipment_to_edit):
            sg.popup_ok(shipment_to_edit.address_as_str)

        elif event == keys_and_strings.DROPOFF_KEY(shipment_to_edit):
            new_date = dropoff_click(config=config, shipment=shipment_to_edit)
            if new_date is None:
                continue
            window[keys_and_strings.DATE_KEY(shipment_to_edit)].update(new_date)
            window[event].update(button_color='red')

        else:
            sg.popup_error(f'Wrong event code from pysimplegui listener = {event}')

        if package:
            window[event].update(package)


def read_window_cboxs(values, shipment):
    """Gets values from pysimplegui checkboxes"""
    shipment.is_to_print_email = values.get(keys_and_strings.PRINT_EMAIL_KEY(shipment))
    shipment.is_to_book = values.get(keys_and_strings.BOOK_KEY(shipment))
    return shipment


def print_email_label(print_email: bool, email_body, shipment: ShipmentQueued):
    """prints or emails label"""
    shipment.is_printed = False
    shipment.is_emailed = False

    if not print_email:
        return

    if shipment.is_outbound:
        print_label(shipment=shipment)
        shipment.is_printed = True
    else:
        email_label(shipment=shipment,
                    body=email_body,
                    collection_date=shipment.collection_return.date,
                    collection_address=shipment.collection_return.sender_address.sender_address)
        shipment.is_emailed = True


def queue_shipment(shipment: ShipmentRequested) -> ShipmentQueued:
    """queues shipment with despatch bay api"""
    shipment.shipment_request = get_shipment_request(shipment=shipment)
    shipment.timestamp = f"{datetime.now():{DateTimeMasks.FILE.value}}"
    shipment.shipment_id = DESP_CLIENT.add_shipment(shipment.shipment_request)
    shipment.is_queued = True
    setattr(shipment, f'{"outbound_id" if shipment.is_outbound else "inbound_id"}', shipment.shipment_id)
    queued_shipment = ShipmentQueued(**shipment.__dict__, **shipment.model_extra)
    return queued_shipment


def book_shipment(shipment: ShipmentQueued) -> ShipmentBooked:
    """books shipment with despatch bay api"""
    try:
        shipment.shipment_return = DESP_CLIENT.book_shipments(shipment.shipment_id)[0]

    except ApiException as e:
        sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\nAvailable balance = "
                       f"£{DESP_CLIENT.get_account_balance().available}\n{e}\n")
        raise e
    except Exception as e:
        sg.popup_error(f"Unable to Book {shipment.shipment_name_printable} due to: {e.args}")
        logger.exception(e)
        raise e
    else:
        shipment.collection_return = DESP_CLIENT.get_collection(shipment.shipment_return.collection_id)
        shipment.is_booked = True
        booked_shipment = ShipmentBooked(**shipment.__dict__, **shipment.model_extra)
        return booked_shipment


def get_collection_date(shipment: ShipmentPrepared, available_dates: List[CollectionDate]) -> CollectionDate:
    """ Matches shipment send_out_date to available collections, or uses first available if no match """

    for display, potential_date in shipment.date_menu_map.items():
        if collection_date_to_datetime(potential_date) == shipment.send_out_date:
            collection_date = potential_date
            shipment.date_matched = True
            break
    else:
        collection_date = available_dates[0]
        shipment.date_matched = False

    logger.info(f'COLLECTION DATE {"NOT" if not shipment.date_matched else ""} MATCHED')
    return collection_date


def get_actual_service(shipment, default_service_id: str, available_services: [Service]) -> Service:
    """gets matching service or first available"""
    for service in available_services:
        if service.service_id == default_service_id:
            shipment.default_service_matched = True
            return service
    else:
        shipment.default_service_matched = False
        return available_services[0]


def get_shipment_request(shipment: ShipmentForRequest) -> ShipmentRequest:
    """ returns a shipment_request from shipment object"""
    label_text = shipment.customer_printable
    if not shipment.is_outbound:
        label_text += ' RTN'
    request = DESP_CLIENT.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=label_text,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )
    logger.info(f'SHIPMENT REQUEST:\n{request}')
    return request


def download_label(label_folder_path: Path, label_text: str, doc_id: str):
    """" downlaods labels from given doc_id to given folder path"""

    try:
        label_pdf: Document = DESP_CLIENT.get_labels(document_ids=doc_id,
                                                     label_layout='2A4')

        label_string: str = label_text.replace(':', '') + '.pdf'
        label_location = label_folder_path / label_string
        label_pdf.download(label_location)
    except:
        return False
    else:
        return label_location

def download_shipment_label(shipment:ShipmentBooked, config:Config):
    """" downlaods labels from given doc_id to given folder path"""
    doc_id = shipment.shipment_return.shipment_document_id

    if shipment.is_outbound:
        label_folder = config.paths.outbound_labels
        label_filename = shipment.label_filename_outbound
    else:
        label_folder = config.paths.inbound_labels
        label_filename = shipment.label_filename_inbound


    try:
        label_pdf: Document = DESP_CLIENT.get_labels(document_ids=doc_id,
                                                     label_layout='2A4')

        label_filename: str = label_filename.replace(':', '') + '.pdf'
        label_location = label_folder / label_filename
        label_pdf.download(label_location)
    except:
        logger.warning(f'Unable to download label for {shipment.shipment_name_printable}')
        return False
    else:
        return label_location


def commence_package_sale(shipment: ShipmentQueued):
    """returns dict to update database with collection details"""
    return {'Delivery Notes': f'PF label printed {datetime.today().date().isoformat()} [AD]'}


def commence_package_hire(shipment: ShipmentQueued):
    """returns dict to update database with collection details"""
    cmc_update_package = {}
    if shipment.is_outbound:
        cmc_update_package['DB label printed'] = True
    else:
        cmc_update_package[
            'Return Notes'] = f'PF coll booked for {shipment.collection_date_datetime:{DateTimeMasks.HIRE.value}} on {datetime.today().date():{DateTimeMasks.HIRE.value}} [AD]'
        cmc_update_package['Pickup Arranged'] = True

    return cmc_update_package


def maybe_update_commence(config: Config, shipment: ShipmentQueued):
    """ updates commence if shipment is hire/sale"""

    if config.sandbox:
        if sg.popup_yes_no("Sandbox mode: Update Commence Anyway?") != 'Yes':
            return ShipmentCmcUpdated(**shipment.__dict__, **shipment.model_extra, is_logged_to_commence=False)

    id_to_store = 'Outbound ID' if shipment.is_outbound else 'Inbound ID'
    cmc_update_package = {id_to_store: shipment.shipment_id}

    if shipment.category == ShipmentCategory.HIRE:
        cmc_update_package.update(commence_package_hire(shipment))

    elif shipment.category == ShipmentCategory.SALE:
        cmc_update_package.update(commence_package_sale(shipment))

    else:
        logger.warning(f'Category {shipment.category} not recognised for commence updater')
        return shipment

    result = edit_commence(pscript=config.paths.cmc_updater, table=shipment.category.value,
                           record=shipment.shipment_name,
                           package=cmc_update_package, function=PS_FUNCS.APPEND.value)
    if result.returncode == 0:
        shipment.is_logged_to_commence = True
        return ShipmentCmcUpdated(**shipment.__dict__, **shipment.model_extra)
    else:
        shipment.is_logged_to_commence = False
        return shipment


def tracking_loop(shipments: List[ShipmentRequested]):
    for shipment in shipments:
        if outbound_id := shipment.outbound_id:
            outbound_window = get_tracking(outbound_id)
            event, values = outbound_window.read()
        if inbound_id := shipment.inbound_id:
            inbound_window = get_tracking(inbound_id)
            event, values = inbound_window.read()


def track():
    # tracking_loop(shipments=self.shipments)
    # track2(shipments=self.shipments)
    ...
