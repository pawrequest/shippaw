import sys
from datetime import datetime
from pathlib import Path
from typing import List, cast

import PySimpleGUI as sg
import dotenv
from dbfread import DBF, DBFNotFound
from despatchbay.despatchbay_entities import CollectionDate, Service, ShipmentReturn
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from core.config import Config, logger
from core.desp_client_wrapper import APIClientWrapper
from core.enums import ShipmentCategory
from core.funcs import collection_date_to_datetime, email_label, log_shipment, print_label, update_commence
from gui import keys_and_strings
from gui.main_gui import main_window, post_book
from shipper.addresser import address_shipments
from shipper.edit_shipment import address_click, boxes_click, date_click, dropoff_click, get_parcels, service_click
from shipper.shipment import Shipment, shipdict_from_dbase
from shipper.tracker import get_tracking

dotenv.load_dotenv()
DESP_CLIENT: DespatchBaySDK | None = None


class Shipper:
    def __init__(self, config):
        global DESP_CLIENT
        client = DespatchBaySDK(api_user=config.dbay_creds.api_user, api_key=config.dbay_creds.api_key)
        client = APIClientWrapper(client)
        client = cast(DespatchBaySDK, client)
        DESP_CLIENT = client
        self.shipments: list[Shipment] = []
        self.config = config

    def get_shipments(self, category: ShipmentCategory, dbase_file: str):
        logger.info(f'DBase file og = {dbase_file}')
        try:
            for record in DBF(dbase_file, encoding='cp1252'):
                [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
                try:
                    ship_dict = shipdict_from_dbase(record=record, import_mapping=self.config.import_mapping)
                    self.shipments.append(Shipment(ship_dict=ship_dict, category=category))
                except Exception as e:
                    logger.exception(f'{record.__repr__()} - {e}')
                    continue

        except UnicodeDecodeError as e:
            logger.exception(f'DBASE import error with {dbase_file} \n {e}')
        except DBFNotFound as e:
            logger.exception(f'.Dbf or Dbt are missing \n{e}')
        except Exception as e:
            logger.exception(e)
            raise

    def dispatch(self):
        config = self.config
        shipments = self.shipments
        address_shipments(outbound=config.outbound, shipments=shipments, config=config)
        [gather_dbay_objs(shipment=shipment, config=config) for shipment in shipments]
        booked_shipments = dispatch_loop(config=config, shipments=shipments)
        post_book(shipments=booked_shipments)

    def track(self):
        tracking_loop(shipments=self.shipments)


def tracking_loop(shipments: List[Shipment]):
    for shipment in shipments:
        if outbound_id := shipment.outbound_id:
            outbound_window = get_tracking(outbound_id)
            event, values = outbound_window.read()
        if inbound_id := shipment.inbound_id:
            inbound_window = get_tracking(inbound_id)
            event, values = inbound_window.read()


def dispatch_loop(config, shipments: List[Shipment]):
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

        shipment_to_edit: Shipment = next((shipment for shipment in shipments if
                                           shipment.shipment_name_printable.lower() in event.lower()))

        if event == keys_and_strings.GO_SHIP_KEY():
            if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                sg.popup_quick_message('Please Wait')
                window.close()
                return process_shipments(shipments=shipments, values=values, config=config)

        elif event == keys_and_strings.BOXES_KEY(shipment_to_edit):
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
            sg.popup_ok(shipment_to_edit._address_as_str)

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


def process_shipments(shipments, values, config):
    booked_shipments = []

    for shipment in shipments:
        shipment.shipment_request = get_shipment_request(shipment=shipment)
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        shipment_id = DESP_CLIENT.add_shipment(shipment.shipment_request)

        if values.get(keys_and_strings.BOOK_KEY(shipment)):
            try:
                booked_shipments.append(
                    book_shipment(shipment=shipment, shipment_id=shipment_id, config=config, values=values))

            except ApiException as e:
                sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\nAvailable balance = "
                               f"£{DESP_CLIENT.get_account_balance().available}\n{e}\n")
                continue
            except Exception as e:
                sg.popup_error(f"Unable to Book {shipment.shipment_name_printable} due to: {e.args}")

                logger.exception(e)
                continue

        log_shipment(log_path=config.paths.log_json, shipment=shipment)

    return booked_shipments if booked_shipments else None


def book_shipment(config, values, shipment: Shipment, shipment_id):
    outbound = config.outbound
    shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"

    print_email = values.get(keys_and_strings.PRINT_EMAIL_KEY(shipment))

    setattr(shipment, f'{"outbound_id" if outbound else "inbound_id"}', shipment_id)

    shipment.shipment_return = DESP_CLIENT.book_shipments(shipment_id)[0]
    shipment.label_location = download_label(label_folder_path=config.paths.labels,
                                             label_text=shipment.shipment_name_printable,
                                             shipment_return=shipment.shipment_return)
    shipment.collection_return = DESP_CLIENT.get_collection(shipment.shipment_return.collection_id)

    if outbound and print_email:
        print_label(shipment=shipment)
    else:
        if not outbound and print_email:
            email_label(shipment=shipment,
                        body=config.return_label_email_body,
                        collection_date=shipment.collection_return.date,
                        collection_address=shipment.collection_return.sender_address.sender_address
                        )
    update_commence(shipment=shipment, id_to_pass=shipment_id, outbound=config.outbound,
                    ps_script=config.paths.cmc_logger)
    return shipment


def get_collection_date(shipment: Shipment, courier_id) -> CollectionDate:
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
        f'PREPPING SHIPMENT - COLLECTION DATE {collection_date.date}{" - DATE MATCHED" if shipment.date_matched else ""}')
    return collection_date


def get_actual_service(default_service_id: str, available_services: [Service]) -> Service:
    """returns the service object for the default service id if it exists, otherwise returns the first service"""
    return next((service for service in available_services if service.service_id == default_service_id),
                available_services[0])


def get_shipment_request(shipment: Shipment):
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


def gather_dbay_objs(shipment: Shipment, config: Config):
    client = DESP_CLIENT
    shipment.service = client.get_services()[0]  # needed to get dates
    shipment.collection_date = get_collection_date(shipment=shipment,
                                                   courier_id=config.default_shipping_service.courier)
    shipment.parcels = get_parcels(num_parcels=shipment.boxes)
    shipment.shipment_request = get_shipment_request(shipment=shipment)
    shipment.available_services = client.get_available_services(shipment.shipment_request)
    shipment.service = get_actual_service(default_service_id=config.default_shipping_service.service,
                                          available_services=shipment.available_services)


def download_label(label_folder_path: Path, label_text: str, shipment_return: ShipmentReturn):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in user_config.toml"""
    try:
        label_pdf: Document = DESP_CLIENT.get_labels(document_ids=shipment_return.shipment_document_id,
                                                     label_layout='2A4')

        label_string: str = label_text + '.pdf'
        label_location = label_folder_path / label_string
        label_pdf.download(label_location)
    except:
        return False
    else:
        return label_location
