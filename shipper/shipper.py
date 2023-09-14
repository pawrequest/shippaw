import sys
from datetime import datetime
from pathlib import Path
from typing import List

import PySimpleGUI as sg
import dotenv
from despatchbay.despatchbay_entities import CollectionDate, Service, ShipmentRequest
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from core.cmc_updater import PS_FUNCS, edit_commence
from core.config import Config, logger
from core.enums import Contact, DateTimeMasks, HomeAddress, ShipmentCategory
from core.funcs import collection_date_to_datetime, email_label, print_label
from gui import keys_and_strings
from gui.main_gui import main_window, post_book
from shipper.addresser import get_home_sender_recip, get_remote_recipient, remote_address_script, \
    sender_from_contact_address
from shipper.edit_shipment import address_click, date_click, dropoff_click, get_new_boxes, get_parcels, \
    service_click, \
    update_service_button
from shipper.shipment import ShipmentAddressed, ShipmentBooked, ShipmentCmcUpdated, ShipmentCompleted, \
    ShipmentGuiConfirmed, ShipmentInput, ShipmentPreRequest, ShipmentPrepared, ShipmentQueued, ShipmentRequested
from shipper.tracker import get_tracking

dotenv.load_dotenv()


class Shipper:
    def __init__(self, config: Config, shipments: List[ShipmentInput], client: DespatchBaySDK):
        self.config = config
        self.shipments = shipments
        self.client = client


def dispatch(config: Config, client: DespatchBaySDK, prepared_shipments: List[ShipmentRequested]):
    """ Shipment processing pipeline - takes list of validated shipments and Config objects,
    walks through addressing and preparation steps before selectively booking collecitons and printing labels as per GUI"""

    shipments_complete = gui_listener(config=config, shipments=prepared_shipments, client=client)
    post_book(shipments=shipments_complete)


def prepare_batch(client, config, shipments):
    shipments_addressed = [address_shipment(shipment=shipment, home_address=config.home_address,
                                            home_contact=config.home_contact, client=client) for shipment in shipments]
    shipments_prepared = [
        prepare_shipment(shipment=shipment, default_courier=config.default_carrier.courier, client=client)
        for shipment in shipments_addressed]
    shipments_for_request = [pre_request_shipment(default_shipping_service_id=config.default_carrier.service,
                                                  shipment=shipment, client=client) for shipment in shipments_prepared]
    shipments_requested = [request_shipment(shipment=shipment, client=client) for shipment in shipments_for_request]
    return shipments_requested


def address_shipment(shipment: ShipmentInput, home_address: HomeAddress, home_contact: Contact,
                     client: DespatchBaySDK) -> ShipmentAddressed:
    """ gets Contact, Address, Sender and Recipient objects"""
    remote_contact = Contact(name=shipment.contact_name, email=shipment.email, telephone=shipment.telephone)
    remote_address = remote_address_script(shipment=shipment, remote_contact=remote_contact, client=client)
    if shipment.is_outbound:
        sender = get_home_sender_recip(home_contact=home_contact, home_address=home_address,
                                       outbound=shipment.is_outbound, client=client)
        recipient = get_remote_recipient(contact=remote_contact,
                                         remote_address=remote_address, client=client)
    else:
        sender = sender_from_contact_address(contact=remote_contact,
                                             remote_address=remote_address, client=client)
        recipient = get_home_sender_recip(home_contact=home_contact, home_address=home_address,
                                          outbound=shipment.is_outbound, client=client)
    return ShipmentAddressed(**shipment.__dict__, remote_contact=remote_contact, sender=sender, recipient=recipient,
                             remote_address=remote_address)


def prepare_shipment(shipment: ShipmentAddressed, default_courier, client) -> ShipmentPrepared:
    """ Gets objects for all available CollectionDates and Services, creates menu maps for gui"""
    available_dates = client.get_available_collection_dates(sender_address=shipment.sender,
                                                            courier_id=default_courier)
    all_services = client.get_services()
    date_menu_map = keys_and_strings.DATE_MENU(available_dates)
    service_menu_map = keys_and_strings.SERVICE_MENU(all_services)

    return ShipmentPrepared(**shipment.__dict__, available_dates=available_dates, all_services=all_services,
                            date_menu_map=date_menu_map, service_menu_map=service_menu_map)


def pre_request_shipment(shipment: ShipmentPrepared, default_shipping_service_id,
                         client: DespatchBaySDK) -> ShipmentPreRequest:
    """ gets actual CollectionDate, Service and Parcel objects"""
    shipment.parcels = get_parcels(num_parcels=shipment.boxes, client=client)
    shipment.collection_date = get_collection_date(shipment=shipment, available_dates=shipment.available_dates)

    # need a shipment_request to get a service, need a service to get a shipment_request.... (thanks dbay)
    # so make a temp request using first available service, then match the one we want later
    temp_request = client.shipment_request(
        service_id=default_shipping_service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer_printable,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )

    available_services = client.get_available_services(temp_request)
    shipment.service = get_actual_service(default_service_id=default_shipping_service_id,
                                          available_services=available_services, shipment=shipment)

    return ShipmentPreRequest(**shipment.__dict__, **shipment.model_extra)


def request_shipment(shipment: ShipmentPreRequest, client:DespatchBaySDK) -> ShipmentRequested:
    """ gets shipment request"""
    shipment.shipment_request = get_shipment_request(shipment=shipment, client=client)
    return ShipmentRequested(**shipment.__dict__ | shipment.model_extra)


def process_shipment(shipment_req: ShipmentRequested, values: dict, config: Config, client:DespatchBaySDK) -> ShipmentBooked | ShipmentQueued:
    """ queues and books shipment, updates commence, prints and emails label"""
    if not sg.popup_yes_no("Queue and book shipments?") == 'Yes':
        if sg.popup_ok_cancel("Ok to quit, cancel to continue booking") == 'OK':
            logger.info('User quit')
            sys.exit()
    shipment: ShipmentGuiConfirmed = read_window_cboxs(shipment=shipment_req, values=values)
    shipment: ShipmentQueued = queue_shipment(shipment=shipment, client=client)
    shipment: ShipmentCmcUpdated = update_commence(config=config, shipment=shipment)
    if not shipment.is_to_book:
        return shipment
    shipment: ShipmentBooked = book_shipment(shipment=shipment, client=client)
    shipment.label_location = download_shipment_label(shipment=shipment, config=config, client=client)
    print_email_label(print_email=shipment.is_to_print_email, email_body=config.return_label_email_body,
                      shipment=shipment)
    booked = ShipmentCompleted(**shipment.__dict__, **shipment.model_extra)

    return booked


def gui_listener(config: Config, shipments: List[ShipmentRequested], client:DespatchBaySDK) -> List[ShipmentBooked | ShipmentQueued]:
    """ pysimplegui main_loop, takes list of ShipmentRequested objects
    listens for user input to edit and update shipments
    listens for go_ship  button to start booking collection etc"""
    logger.info('GUI LOOP')

    if config.sandbox:
        sg.theme('Tan')
    else:
        sg.theme('Dark Blue')

    window = main_window(shipments=shipments)
    processed_shipments = []

    while True:
        package = None
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            window.close()
            sys.exit()

        if event == keys_and_strings.GO_SHIP_KEY():
            window.close()

            sg.popup_quick_message('Processing shipments, please wait...')
            for shipment in shipments:
                processed_shipments.append(process_shipment(shipment_req=shipment, values=values, config=config, client=client))
            return processed_shipments

        # todo if values[event] == shipment_to_edit ie make .eq() in shipmentinput
        shipment_to_edit_index = next(
            (i for i, shipment in enumerate(shipments) if keys_and_strings.SHIPMENT_KEY(shipment) in event.upper()),
            None)

        # shipment_to_edit: ShipmentRequested = next((shipment for shipment in shipments if
        #                                             keys_and_strings.SHIPMENT_KEY(shipment) in event.upper()))
        shipment_to_edit = shipments[shipment_to_edit_index]

        if event == keys_and_strings.BOXES_KEY(shipment_to_edit):
            new_boxes = get_new_boxes(location=window.mouse_location())
            if new_boxes is None:
                continue
            shipment_to_edit.parcels = get_parcels(num_parcels=new_boxes, client=client)
            update_service_button(num_boxes=new_boxes, shipment_to_edit=shipment_to_edit, window=window)
            package = new_boxes

        elif event == keys_and_strings.SERVICE_KEY(shipment_to_edit):
            shipment_to_edit = request_shipment(shipment_to_edit, client=client)  # update available services in case address changed
            package = service_click(shipment_to_edit=shipment_to_edit, location=window.mouse_location(),
                                    default_service=shipment_to_edit.service, client=client)
            # shipment_to_edit = request_shipment(shipment_to_edit) # update available services in case address changed
            ...

        elif event == keys_and_strings.DATE_KEY(shipment_to_edit):
            package = date_click(location=window.mouse_location(), shipment_to_edit=shipment_to_edit)

        elif event == keys_and_strings.SENDER_KEY(shipment_to_edit):
            package = address_click(shipment=shipment_to_edit, target=shipment_to_edit.sender)

        elif event == keys_and_strings.RECIPIENT_KEY(shipment_to_edit):
            package = address_click(shipment=shipment_to_edit, target=shipment_to_edit.recipient)

        elif event == keys_and_strings.REMOVE_KEY(shipment_to_edit):
            shipments = [s for s in shipments if s != shipment_to_edit]
            window.close()
            window = main_window(shipments=shipments)

        elif event == keys_and_strings.CUSTOMER_KEY(shipment_to_edit):
            sg.popup_ok(shipment_to_edit.address_as_str)

        elif event == keys_and_strings.DROPOFF_KEY(shipment_to_edit):
            new_date = dropoff_click(config=config, shipment=shipment_to_edit, client=client)
            if new_date is None:
                continue
            window[keys_and_strings.DATE_KEY(shipment_to_edit)].update(new_date)
            window[event].update(button_color='red')

        else:
            sg.popup_error(f'Wrong event code from pysimplegui listener = {event}')

        if package:
            window[event].update(package)
        shipments[shipment_to_edit_index] = shipment_to_edit


def shipment_editor(shipment_to_edit, window, event, values):
    # handler dict?
    ...


def read_window_cboxs(values, shipment):
    """Gets values from pysimplegui checkboxes"""
    shipment.is_to_print_email = values.get(keys_and_strings.PRINT_EMAIL_KEY(shipment))
    shipment.is_to_book = values.get(keys_and_strings.BOOK_KEY(shipment))
    """ reads gui checkboxes"""
    return ShipmentGuiConfirmed(**shipment.model_dump())



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


def queue_shipment(shipment: ShipmentRequested, client: DespatchBaySDK) -> ShipmentQueued:
    """queues shipment with despatch bay api"""
    shipment.shipment_request = get_shipment_request(shipment=shipment, client=client)
    shipment.timestamp = f"{datetime.now():{DateTimeMasks.FILE.value}}"
    shipment.shipment_id = client.add_shipment(shipment.shipment_request)
    shipment.is_queued = True
    setattr(shipment, f'{"outbound_id" if shipment.is_outbound else "inbound_id"}', shipment.shipment_id)
    return ShipmentQueued(**shipment.__dict__, **shipment.model_extra)


def book_shipment(shipment: ShipmentQueued, client: DespatchBaySDK) -> ShipmentBooked:
    """books shipment with despatch bay api"""
    try:
        shipment.shipment_return = client.book_shipments(shipment.shipment_id)[0]

    except ApiException as e:
        sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\nAvailable balance = "
                       f"£{client.get_account_balance().available}\n{e}\n")
        raise e
    except Exception as e:
        sg.popup_error(f"Unable to Book {shipment.shipment_name_printable} due to: {e.args}")
        logger.exception(e)
        raise e
    else:
        shipment.collection_return = client.get_collection(shipment.shipment_return.collection_id)
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


def get_shipment_request(shipment: ShipmentPreRequest, client: DespatchBaySDK) -> ShipmentRequest:
    """ returns a shipment_request from shipment object"""
    label_text = shipment.customer_printable
    if not shipment.is_outbound:
        label_text += ' RTN'
    request = client.shipment_request(
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


def download_shipment_label(shipment: ShipmentBooked, config: Config, client: DespatchBaySDK) -> Path | bool:
    """" downlaods labels from given doc_id to given folder path"""
    doc_id = shipment.shipment_return.shipment_document_id

    label_path = get_label_path(config, shipment)

    try:
        label_pdf: Document = client.get_labels(document_ids=doc_id,
                                                label_layout='2A4')

        label_pdf.download(label_path)
    except:
        logger.warning(f'Unable to download label for {shipment.shipment_name_printable} to {label_path}')
    else:
        return label_path


def get_label_path(config: Config, shipment: ShipmentBooked) -> Path:
    if shipment.is_outbound:
        label_folder = config.paths.outbound_labels
        label_filename = shipment.label_filename_outbound
    else:
        label_folder = config.paths.inbound_labels
        label_filename = shipment.label_filename_inbound
    label_filename: str = label_filename.replace(':', '') + '.pdf'
    label_path = label_folder / label_filename
    return label_path


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


def update_commence(config: Config, shipment: ShipmentQueued):
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

    elif shipment.category == ShipmentCategory.CUSTOMER:
        shipment.is_logged_to_commence = False
        logger.warning(f'Category "Customer" not implemented for commence updater')
        return shipment

    else:
        logger.warning(f'Category {shipment.category} not recognised for commence updater')
        shipment.is_logged_to_commence = False
        return shipment

    result = edit_commence(pscript=str(config.paths.cmc_updater), table=shipment.category.value,
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
