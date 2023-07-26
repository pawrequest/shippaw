import sys
from datetime import datetime
from pathlib import Path
from typing import List, cast

import PySimpleGUI as sg
import dotenv
from dbfread import DBF, DBFNotFound
from despatchbay.despatchbay_entities import CollectionDate, Parcel, Service, Recipient, Sender, ShipmentReturn, Address
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from core.config import Config, logger
from core.desp_client_wrapper import APIClientWrapper
from core.enums import Contact, DateTimeMasks, ShipmentCategory
from core.funcs import email_label, log_shipment, print_label, update_commence, collection_date_to_datetime

from gui import psg_keys
from gui.address_gui import address_from_gui
from gui.main_gui import get_date_label, get_service_string, get_address_button_string, new_date_selector, \
    new_service_selector, get_new_parcels_window, post_book, main_window
from shipper.addresser import fuzzy_address, address_from_direct_search, sender_from_address_id, \
    recip_from_contact_and_key, sender_from_contact_address, recip_from_contact_address
from shipper.shipment import Shipment, shipdict_from_dbase

dotenv.load_dotenv()
CLIENT: DespatchBaySDK | None = None


class Shipper:
    def __init__(self, config):
        global CLIENT
        client = DespatchBaySDK(api_user=config.dbay_creds.api_user, api_key=config.dbay_creds.api_key)
        client = APIClientWrapper(client)
        client = cast(DespatchBaySDK, client)
        CLIENT = client

    @staticmethod
    def get_shipments(config: Config, category: ShipmentCategory, dbase_file: str) -> list[Shipment]:
        logger.info(f'DBase file og = {dbase_file}')
        shipments: [Shipment] = []
        try:
            for record in DBF(dbase_file, encoding='cp1252'):
                [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
                try:
                    ship_dict = shipdict_from_dbase(record=record, import_mapping=config.import_mapping)
                    shipment = Shipment(ship_dict=ship_dict, category=category)
                    shipments.append(shipment)
                except Exception as e:
                    logger.exception(f'{record.__repr__()} - {e}')
                    continue

        except UnicodeDecodeError as e:
            logger.exception(f'DBASE import error with {dbase_file} \n {e}')
        except DBFNotFound as e:
            logger.exception(f'.Dbf or Dbt are missing \n{e}')
        except Exception as e:
            logger.exception(e)
            raise e
        return shipments

    @staticmethod
    def dispatch(shipments, config):
        address_shipments(outbound=config.outbound, shipments=shipments, config=config)
        [gather_dbay_objs(shipment=shipment, config=config) for shipment in shipments]
        booked_shipments = dispatch_loop(config=config, shipments=shipments)
        post_book(shipments=booked_shipments)


def dispatch_loop(config, shipments: List[Shipment]):
    """ pysimplegui main_loop, takes a prebuilt window and shipment list,
    listens for user input to edit and update shipments
    listens for go_ship  button to start booking"""
    logger.info('GUI LOOP')

    window = main_window(shipments=shipments, config=config)

    while True:
        package = None
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            window.close()
            sys.exit()
        elif event == event == psg_keys.GO_SHIP():
            if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                sg.popup_quick_message('Please Wait')
                window.close()
                return process_shipments(shipments=shipments, values=values, config=config)
        else:
            shipment_to_edit: Shipment = next((shipment for shipment in shipments if
                                               shipment.shipment_name_printable.lower() in event.lower()))

            if event == psg_keys.BOXES(shipment_to_edit):
                package = boxes_click(shipment_to_edit=shipment_to_edit, window=window)

            elif event == psg_keys.SERVICE(shipment_to_edit):
                package = service_click(shipment_to_edit=shipment_to_edit, location=window.mouse_location())

            elif event == psg_keys.DATE(shipment_to_edit):
                package = date_click(location=window.mouse_location(), shipment_to_edit=shipment_to_edit)

            elif event == psg_keys.SENDER(shipment_to_edit):
                package = address_click(shipment=shipment_to_edit, target=shipment_to_edit.sender)

            elif event == psg_keys.RECIPIENT(shipment_to_edit):
                package = address_click(shipment=shipment_to_edit, target=shipment_to_edit.recipient)

            elif event == psg_keys.REMOVE(shipment_to_edit):
                shipments = [s for s in shipments if s != shipment_to_edit]
                window.close()
                window = main_window(shipments=shipments, config=config)

            elif event == psg_keys.CUSTOMER_CONTACT(shipment_to_edit):
                sg.popup_ok(shipment_to_edit._address_as_str)

            elif event == psg_keys.DROPOFF(shipment_to_edit):
                new_date = make_dropoff(config=config, shipment=shipment_to_edit)
                if new_date is None:
                    continue
                window[psg_keys.DATE(shipment_to_edit)].update(new_date)
                window[event].update(button_color='red')

            if package:
                window[event].update(package)


def address_shipments(shipments: list[Shipment], config: Config, outbound: bool):
    """Sets Contact and Address for sender and recipient for each shipment in self.shipments
    home_base is sender if outbound else recipient, other address from remote_address_Script"""
    if not all([config.home_contact, config.home_address.dbay_key]):
        raise ValueError(f"Home Contact or Dbay Key Missing - please edit .toml file")

    home_base = get_home_base(outbound=outbound, config=config)

    for shipment in shipments:
        shipment.remote_contact = Contact(email=shipment.email, telephone=shipment.telephone,
                                          name=shipment.contact_name)
        shipment.remote_address = remote_address_script(shipment=shipment)

        shipment.recipient = recip_from_contact_address(contact=shipment.remote_contact,
                                                        address=shipment.remote_address) if outbound \
            else home_base

        shipment.sender = home_base if outbound \
            else sender_from_contact_address(contact=shipment.remote_contact,
                                             remote_address=shipment.remote_address)


def process_shipments(shipments, values, config):
    booked_shipments = []

    for shipment in shipments:
        shipment.shipment_request = get_shipment_request(shipment=shipment)
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        shipment_id = CLIENT.add_shipment(shipment.shipment_request)

        if values.get(psg_keys.BOOK(shipment)):
            try:
                booked_shipments.append(
                    book_shipment(shipment=shipment, shipment_id=shipment_id, config=config, values=values))

            except ApiException as e:
                sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\nAvailable balance = "
                               f"£{CLIENT.get_account_balance().available}\n{e}\n")
                continue
            except Exception as e:
                logger.exception(e)
                continue

        log_shipment(log_path=config.paths.log_json, shipment=shipment)

    return booked_shipments if booked_shipments else None


def book_shipment(config, values, shipment: Shipment, shipment_id):
    outbound = config.outbound
    shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"

    print_email = values.get(psg_keys.PRINT_EMAIL(shipment))

    setattr(shipment, f'{"outbound_id" if outbound else "inbound_id"}', shipment_id)

    shipment.shipment_return = CLIENT.book_shipments(shipment_id)[0]
    shipment.label_location = download_label(label_folder_path=config.paths.labels,
                                             label_text=shipment.shipment_name_printable,
                                             shipment_return=shipment.shipment_return)
    shipment.collection_return = CLIENT.get_collection(shipment.shipment_return.collection_id)

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


def remote_address_script(shipment:Shipment) -> Address:
    terms = {shipment.customer, shipment.delivery_name, shipment.str_to_match}

    if address := address_from_direct_search(postcode=shipment.postcode, search_terms=terms):
        return address
    logger.info({'No Explicit Match Found - getting fuzzy'})
    fuzzy = fuzzy_address(shipment=shipment)
    while True:
        address = address_from_gui(shipment=shipment, address=fuzzy, contact=shipment.remote_contact)
        if address is None:
            continue
        else:
            return address


def make_dropoff(config, shipment: Shipment):
    if sg.popup_yes_no('Convert To Dropoff? (y/n) (Shipment will NOT be collected!') != 'Yes':
        return None
    logger.info('Converting to Dropoff')
    shipment.sender = sender_from_address_id(address_id=config.home_address.dropoff_sender_id)
    available_dates = CLIENT.get_available_collection_dates(sender_address=shipment.sender,
                                                            courier_id=config.default_shipping_service.courier)
    shipment.date_menu_map = menu_map_from_dates(dates=available_dates)
    new_date = available_dates[0]
    shipment.available_dates = available_dates
    if sg.popup_yes_no(f'Change date to {new_date.date}?') == 'Yes':
        shipment.collection_date = new_date
        return get_date_label(new_date)


def menu_map_from_dates(dates):
    menu_map = {}
    for potential_collection_date in dates:
        real_date = datetime.strptime(potential_collection_date.date, DateTimeMasks.DB.value).date()
        display_date = real_date.strftime(DateTimeMasks.DISPLAY.value)
        menu_map.update({display_date: potential_collection_date})
    return menu_map


def get_collection_date(shipment: Shipment, courier_id) -> CollectionDate:
    """ return despatchbay CollecitonDate Entity
    make a menu_map of displayable dates to colleciton_date objects to populate gui choosers"""
    available_dates = CLIENT.get_available_collection_dates(sender_address=shipment.sender,
                                                            courier_id=courier_id)
    shipment.available_dates = available_dates

    shipment.date_menu_map = menu_map_from_dates(available_dates)

    collection_date = available_dates[0]

    for display, potential_date in shipment.date_menu_map.items():
        if collection_date_to_datetime(potential_date) == shipment.send_out_date:
            collection_date = potential_date
            shipment.date_matched = True
            break

    logger.info(
        f'PREPPING SHIPMENT - COLLECTION DATE {collection_date.date}{" - DATE MATCHED" if shipment.date_matched else ""}')
    return collection_date


def get_service_menu_map(available_services: List[Service]):
    """returns a dict of service names to service objects"""
    return ({service.name: service for service in available_services})


def get_actual_service(default_service_id: str, available_services: [Service]) -> Service:
    """returns the service object for the default service id if it exists, otherwise returns the first service"""
    return next((service for service in available_services if service.service_id == default_service_id),
                available_services[0])


def get_shipment_request(shipment: Shipment):
    """ returns a dbay shipment request object from shipment"""
    request = CLIENT.shipment_request(
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


def get_parcels(num_parcels: int, contents: str = 'Radios') -> list[Parcel]:
    """ return an array of dbay parcel objects equal to the number of boxes provided
        uses arbitrary sizes because dbay api wont allow skipping even though website does"""
    parcels = []
    for x in range(num_parcels):
        parcel = CLIENT.parcel(
            contents=contents,
            value=500,
            weight=6,
            length=60,
            width=40,
            height=40,
        )
        parcels.append(parcel)
    logger.info(f'PREPPING SHIPMENT - {len(parcels)} PARCELS ')

    return parcels



def get_new_parcels(location, parcel_contents="Radios") -> List[Parcel] | None:
    window = get_new_parcels_window(location=location)
    e, v = window.read()
    if e == sg.WIN_CLOSED:
        window.close()
        return None
    if e == psg_keys.BOX():
        new_boxes = int(v[e])
        window.close()
        return get_parcels(num_parcels=new_boxes, contents=parcel_contents)


def gather_dbay_objs(shipment: Shipment, config:Config):
    client = CLIENT
    shipment.service = client.get_services()[0]  # needed to get dates
    shipment.collection_date = get_collection_date(shipment=shipment, courier_id=config.default_shipping_service.courier)
    shipment.parcels = get_parcels(num_parcels=shipment.boxes)
    shipment.shipment_request = get_shipment_request(shipment=shipment)
    shipment.available_services = client.get_available_services(shipment.shipment_request)
    shipment.service = get_actual_service(default_service_id=config.default_shipping_service.service,
                                          available_services=shipment.available_services)


def boxes_click(shipment_to_edit, window):
    new_parcels = get_new_parcels(location=window.mouse_location())
    if new_parcels is None:
        return None
    shipment_to_edit.parcels = new_parcels
    update_service(new_parcels, shipment_to_edit, window)
    return len(shipment_to_edit.parcels)

    # update_parcels(new_parcels, shipment_to_edit, window)


def update_service(new_parcels, shipment_to_edit, window):
    window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
        f'{shipment_to_edit.service.name} \n£{len(new_parcels) * shipment_to_edit.service.cost:.2f}')


def date_click(location, shipment_to_edit):
    new_collection_date = new_date_selector(shipment=shipment_to_edit,
                                            popup_location=location)
    shipment_to_edit.collection_date = new_collection_date

    return get_date_label(collection_date=new_collection_date)


def address_click(target: Sender | Recipient, shipment: Shipment):
    contact = Contact(name=target.name, email=target.email, telephone=target.telephone)
    if isinstance(target, Sender):
        address_to_edit = shipment.sender.sender_address
    elif isinstance(target, Recipient):
        address_to_edit = shipment.recipient.recipient_address
    else:
        raise TypeError(f'add_click target must be Sender or Recipient, not {type(target)}')

    new_address = address_from_gui(shipment=shipment, address=address_to_edit,
                                   contact=contact)
    if new_address is None:
        return None

    address_to_edit = new_address
    return get_address_button_string(address=address_to_edit)


def service_click(shipment_to_edit, location):
    new_service = new_service_selector(default_service=shipment_to_edit.service.name,
                                       menu_map=get_service_menu_map(
                                           shipment_to_edit.available_services),
                                       location=location)
    if new_service is None:
        return None
    shipment_to_edit.service = new_service
    return get_service_string(service=new_service, num_boxes=len(shipment_to_edit.parcels))


def download_label(label_folder_path: Path, label_text: str, shipment_return: ShipmentReturn):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in user_config.toml"""
    try:
        label_pdf: Document = CLIENT.get_labels(document_ids=shipment_return.shipment_document_id,
                                                label_layout='2A4')

        label_string: str = label_text + '.pdf'
        label_location = label_folder_path / label_string
        label_pdf.download(label_location)
    except:
        return False
    else:
        return label_location


def get_home_base(config, outbound) -> Sender | Recipient:
    """returns a sender object from home_address_id or recipient from home_address.dbay_key representing """
    return CLIENT.sender(address_id=config.home_address.address_id) if outbound \
        else recip_from_contact_and_key(dbay_key=config.home_address.dbay_key,
                                        contact=config.home_contact)


def tracking_loop(ship_ids):
    for shipment_id in ship_ids:
        shipment_return = CLIENT.get_shipment(shipment_id).is_delivered


def track(shipments):
    for shipment in shipments:
        if ship_ids := [shipment.outbound_id, shipment.inbound_id]:
            try:
                tracking_loop(ship_ids=ship_ids)
            except ApiException as e:
                if 'no tracking data' in e.args.__repr__().lower():
                    logger.exception(f'No Tracking Data for {shipment.shipment_name_printable}')
                    sg.popup_error(f'No Tracking data for {shipment.shipment_name_printable}')
                if 'not found' in e.args.__repr__().lower():
                    logger.exception(f'Shipment {shipment.shipment_name_printable} not found')
                    sg.popup_error(f'Shipment ({shipment.shipment_name_printable}) not found')

                else:
                    logger.exception(f'ERROR for {shipment.shipment_name_printable}')
                    sg.popup_error(f'ERROR for {shipment.shipment_name_printable}')

    # def boxes_click(self, event, window):
    #     shipment_to_edit = self.shipment_to_edit
    #     if new_parcels := get_new_parcels(location=window.mouse_location()):
    #         shipment_to_edit.parcels = new_parcels
    #         window[event].update(len(shipment_to_edit.parcels))
    #         window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
    #             f'{shipment_to_edit.service.name} \n£{len(new_parcels) * shipment_to_edit.service.cost:.2f}')
    #
    # def remove_click(self, window, shipment_to_remove):
    #     # [s for s in self.shipments if s.shipment_name_printable != shipment_to_remove.shipment_name_printable]
    #     self.shipments = [s for s in self.shipments if s != shipment_to_remove]
    #     window = self.gui.main_window(shipments=self.shipments, outbound=self.config.outbound,
    #                                   sandbox=self.config.sandbox)
    #
    # def date_click(self):
    #     new_collection_date = new_date_selector(shipment=self.shipment_to_edit,
    #                                             popup_location=self.gui.window.mouse_location())
    #     self.gui.window[event].update(get_date_label(collection_date=new_collection_date))
    #     self.shipment_to_edit.collection_date = new_collection_date
    #
    # def sender_click(self):
    #     send = self.shipment_to_edit.sender
    #     contact = Contact(name=send.name, email=send.email, telephone=send.telephone)
    #     self.sr_click(s_or_r='sender', contact=contact)
    #
    # def recipient_click(self):
    #     rec = self.shipment_to_edit.recipient
    #     contact = Contact(name=rec.name, email=rec.email, telephone=rec.telephone)
    #     self.sr_click(s_or_r='recipient', contact=contact)
    #
    # def sr_click(self, s_or_r, contact):
    #     if s_or_r == 'sender':
    #         address_to_edit = self.shipment_to_edit.sender.sender_address
    #     elif s_or_r == 'recipient':
    #         address_to_edit = self.shipment_to_edit.recipient.recipient_address
    #     else:
    #         raise ValueError('s_or_r must be sender or recipient')
    #
    #     if new_address := get_address(shipment=self.shipment_to_edit, address=address_to_edit,
    #                                   contact=contact):
    #         address_to_edit = new_address
    #         self.gui.window[event].update(get_address_button_string(address=address_to_edit))
    #
    # def service_click(self):
    #     shipment_to_edit = self.shipment_to_edit
    #     if new_service := new_service_selector(default_service=shipment_to_edit.service.name,
    #                                            menu_map=get_service_menu_map(
    #                                                shipment_to_edit.available_services),
    #                                            location=self.gui.window.mouse_location()):
    #         shipment_to_edit.service = new_service
    #         self.gui.window[event].update(get_service_string(service=new_service,
    #                                                          num_boxes=len(shipment_to_edit.parcels)))


