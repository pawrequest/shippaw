import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, cast

import PySimpleGUI as sg
import dotenv
from despatchbay.despatchbay_entities import CollectionDate, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from core.cmc_updater import PS_FUNCS, edit_commence
from core.config import Config, logger
from core.desp_client_wrapper import APIClientWrapper
from core.enums import Contact, DateTimeMasks, ShipmentCategory
from core.funcs import collection_date_to_datetime, email_label, print_label
from gui import keys_and_strings
from gui.main_gui import main_window, post_book
from shipper.addresser import get_home_sender_recip, get_remote_recipient, remote_address_script, \
    sender_from_contact_address
from shipper.edit_shipment import address_click, boxes_click, date_click, dropoff_click, get_parcels, service_click
from shipper.shipment import ShipmentAddressed, ShipmentBooked, ShipmentForRequest, ShipmentGuiConfirmed, ShipmentInput, \
    ShipmentPrepared, ShipmentQueued, ShipmentRequested, records_from_dbase
from shipper.shipments import shipments_from_records
from shipper.tracker import get_tracking

dotenv.load_dotenv()
DESP_CLIENT: DespatchBaySDK | None = None


class Shipper:
    def __init__(self, config: Config):
        global DESP_CLIENT
        try:
            client = DespatchBaySDK(api_user=config.dbay_creds.api_user, api_key=config.dbay_creds.api_key)
        except Exception as e:
            logger.exception(e)
            raise ApiException("Unable to intitialise DespatchBay client")

        client = APIClientWrapper(client)

        client = cast(DespatchBaySDK, client)
        DESP_CLIENT = client
        self.config = config

    def track(self):
        # tracking_loop(shipments=self.shipments)
        # track2(shipments=self.shipments)
        ...


def dispatch(config: Config, shipments: List[ShipmentInput]):
    shipments_addressed: List[ShipmentAddressed] = address_shipments(shipments=shipments, config=config)
    shipments_prepared: List[ShipmentPrepared] = prepare_shipments(shipments=shipments_addressed, config=config)
    shipments_for_request: List[ShipmentForRequest] = shipments_for_requesting(shipments=shipments_prepared,
                                                                               config=config)
    shipments_requested: List[ShipmentRequested] = request_shipments(shipments=shipments_for_request, config=config, )

    shipments_complete = dispatch_loop(config=config, shipments=shipments_requested)
    post_book(shipments=shipments_complete)

    # if not booked_shipments:
    #     logger.warning('No shipments, exiting')
    #     sys.exit()


def dispatch_loop(config: Config, shipments: List[ShipmentRequested]):
    """ pysimplegui main_loop, takes a prebuilt window and shipment list,
    listens for user input to edit and update shipments
    listens for go_ship  button to start booking"""
    logger.info('GUI LOOP')

    if config.sandbox:
        sg.theme('Tan')
    else:
        sg.theme('Dark Blue')

    window = main_window(shipments=shipments, outbound=config.outbound)

    while True:
        package = None
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            window.close()
            sys.exit()

        if event == keys_and_strings.GO_SHIP_KEY():
            if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                sg.popup_quick_message('Please Wait')
                window.close()
                return process_shipments(shipments=shipments, values=values, config=config)
        else:
            logger.info(f'Wrong Event key {event=}')

        # todo if values[event] == shipment_to_edit?
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
    shipment.is_to_print_email = values.get(keys_and_strings.PRINT_EMAIL_KEY(shipment))
    shipment.is_to_book = values.get(keys_and_strings.BOOK_KEY(shipment))
    return shipment


def print_email_label(email_body, shipment):
    if shipment.is_outbound:
        print_label(shipment=shipment)
    else:
        email_label(shipment=shipment,
                    body=email_body,
                    collection_date=shipment.collection_return.date,
                    collection_address=shipment.collection_return.sender_address.sender_address)


def collection_update_package(shipment_id, outbound):
    id_to_store = 'Outbound ID' if outbound else 'Inbound ID'
    cmc_update_package = {id_to_store: shipment_id}
    if outbound:
        cmc_update_package['DB label printed'] = True
    else:
        cmc_update_package['Return Notes'] = f'PF Return booked {datetime.today().date().isoformat()} [AD]'
    return cmc_update_package


def queue_shipment(shipment: ShipmentRequested) -> ShipmentQueued:
    shipment.shipment_request = get_shipment_request(shipment=shipment)
    shipment.timestamp = f"{datetime.now():{DateTimeMasks.filename.value}}"
    shipment_id = DESP_CLIENT.add_shipment(shipment.shipment_request)
    shipment.is_queued = True
    queued_shipment = ShipmentQueued(**shipment.__dict__, shipment_id=shipment_id)
    setattr(shipment, f'{"outbound_id" if shipment.is_outbound else "inbound_id"}', shipment_id)
    return queued_shipment


def book_shipment(shipment: ShipmentQueued) -> ShipmentBooked:
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
        booked_shipment = ShipmentBooked(**shipment.__dict__)
        return booked_shipment


def get_collection_date(shipment: ShipmentInput, courier_id) -> CollectionDate:
    """ return despatchbay CollecitonDate Entity
    make a menu_map of displayable dates to colleciton_date objects to populate gui choosers"""
    available_dates = DESP_CLIENT.get_available_collection_dates(sender_address=shipment.sender,
                                                                 courier_id=courier_id)
    shipment.available_dates = available_dates

    shipment.date_menu_map = keys_and_strings.DATE_MENU(available_dates)

    collection_date = available_dates[0]

    for display, potential_date in shipment.date_menu_map.items():
        if collection_date_to_datetime(potential_date) == shipment.send_out_date:
            collection_date = potential_date
            shipment.date_matched = True
            break

    logger.info(
        f'PREPPING SHIPMENT - COLLECTION DATE {collection_date.date}{" - DATE MATCHED" if shipment.date_matched else "NO DATE MATCH - USING FIRST AVAILABLE"}')
    return collection_date


def get_actual_service(default_service_id: str, available_services: [Service]) -> Service:
    """returns the service object for the default service id if it exists, otherwise returns the first service"""
    return next((service for service in available_services if service.service_id == default_service_id),
                available_services[0])


def get_shipment_request(shipment: ShipmentForRequest) -> ShipmentRequested:
    """ returns a dbay shipment request object from shipment"""
    request = DESP_CLIENT.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer_printable,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )

    logger.info(f'PREPPING SHIPMENT - SHIPMENT REQUEST')
    return request


def download_label(label_folder_path: Path, label_text: str, doc_id: str):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in user_config.toml"""
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


def get_shipments(outbound: bool, import_mappings: dict, category: ShipmentCategory,
                  dbase_file: os.PathLike) -> [ShipmentInput]:
    """ returns a list of validated shipments from a dbase file and a mapping dict"""

    logger.info(f'DBase file og = {dbase_file}')
    import_map_name = f"{category.name.lower()}_mapping"
    import_map = import_mappings[import_map_name]
    logger.info(f'Import map = {import_mappings[import_map_name]}')

    records: [dict] = records_from_dbase(dbase_file)
    shipments: [ShipmentInput] = shipments_from_records(category=category, import_map=import_map, outbound=outbound,
                                                        records=records)
    return shipments


def address_shipments(shipments: List[ShipmentInput], config: Config) -> List[ShipmentAddressed]:
    return [address_shipment(shipment=shipment, config=config) for shipment in shipments]


def address_shipment(shipment: ShipmentInput, config: Config) -> ShipmentAddressed:
    shipment.remote_contact = Contact(name=shipment.contact, email=shipment.email, telephone=shipment.phone)
    shipment.remote_address = remote_address_script(shipment=shipment)
    if shipment.is_outbound:
        shipment.sender = get_home_sender_recip(config=config, outbound=shipment.is_outbound)
        shipment.recipient = get_remote_recipient(contact=shipment.remote_contact,
                                                  remote_address=shipment.remote_address)
    else:
        shipment.sender = sender_from_contact_address(contact=shipment.remote_contact,
                                                      remote_address=shipment.remote_address)
        shipment.recipient = get_home_sender_recip(config=config, outbound=shipment.is_outbound)
    return ShipmentAddressed(**shipment.__dict__)


def prepare_shipments(shipments: List[ShipmentAddressed], config: Config) -> List[ShipmentPrepared]:
    return [prepare_shipment(shipment=shipment, config=config) for shipment in shipments]


def prepare_shipment(shipment: ShipmentAddressed, config: Config) -> ShipmentPrepared:
    client = DESP_CLIENT
    # service = client.get_services()[0]  # needed to get dates isit tho?
    shipment.collection_date = get_collection_date(shipment=shipment,
                                                   courier_id=config.default_shipping_service.courier)
    shipment.parcels = get_parcels(num_parcels=shipment.boxes)

    shipment.shipment_request = get_shipment_request(shipment=shipment)

    shipment.available_services = client.get_available_services(shipment.shipment_request)
    shipment.service = get_actual_service(default_service_id=config.default_shipping_service.service,
                                          available_services=shipment.available_services)
    return ShipmentRequested(**shipment.__dict__)


def shipments_for_requesting(shipments: List[ShipmentPrepared], config: Config) -> List[ShipmentForRequest]:
    return [shipment_requesting(shipment) for shipment in shipments]


def shipment_requesting(shipment: ShipmentPrepared) -> ShipmentForRequest:
    ...


def request_shipments(shipments: List[ShipmentForRequest], config: Config) -> List[ShipmentRequested]:
    return [request_shipment(shipment=shipment, config=config) for shipment in shipments]


def request_shipment(shipment: ShipmentForRequest, config: Config) -> ShipmentRequested:
    shipment.shipment_request = get_shipment_request(shipment=shipment)
    return ShipmentRequested(**shipment.__dict__)


def gui_confirm_shipment(shipment: ShipmentRequested, values: dict) -> ShipmentGuiConfirmed:
    read_window_cboxs(values=values, shipment=shipment)
    return ShipmentGuiConfirmed(**shipment.__dict__)


def process_shipments(shipments: List[ShipmentGuiConfirmed], config: Config) -> List[ShipmentBooked]:
    return [process_shipment(shipment=shipment, config=config) for shipment in shipments]


def process_shipment(shipment: ShipmentGuiConfirmed, config: Config) -> ShipmentBooked | ShipmentQueued:
    queued_shipment: ShipmentQueued = queue_shipment(shipment=shipment)
    maybe_update_commence(cmc_updater_ps1=config.paths.cmc_updater, shipment=shipment)

    if not shipment.is_to_book:
        return queued_shipment
    else:
        booked_shipment = book_shipment(shipment=queued_shipment)
        shipment.label_location = download_label(label_folder_path=config.paths.labels,
                                                 label_text=f'{shipment.shipment_name_printable} - {shipment.timestamp}',
                                                 doc_id=shipment.shipment_return.shipment_document_id)

    if shipment.is_to_print_email:
        print_email_label(email_body=config.return_label_email_body, shipment=shipment)

    return booked_shipment


def maybe_update_commence(cmc_updater_ps1, shipment):
    if shipment.category in ['Hire', 'Sale']:
        cmc_update_package = collection_update_package(shipment_id=shipment.shipment_id, outbound=shipment.is_outbound)
        edit_commence(pscript=cmc_updater_ps1, table=shipment.category.value, record=shipment.shipment_name,
                      package=cmc_update_package, function=PS_FUNCS.APPEND.value)
        shipment.logged_to_commence = True


def tracking_loop(shipments: List[ShipmentRequested]):
    for shipment in shipments:
        if outbound_id := shipment.outbound_id:
            outbound_window = get_tracking(outbound_id)
            event, values = outbound_window.read()
        if inbound_id := shipment.inbound_id:
            inbound_window = get_tracking(inbound_id)
            event, values = inbound_window.read()
