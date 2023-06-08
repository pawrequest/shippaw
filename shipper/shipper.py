"""
rules of thumb
shipper has the client, if you dont need the client, you are not shipper
guis dont have clients

"""

import sys
from datetime import datetime
from typing import List, Optional

import PySimpleGUI as sg
import dotenv
from despatchbay.despatchbay_entities import CollectionDate, Parcel, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException

from core.config import Config, get_amdesp_logger
from core.enums import Contact, DateTimeMasks
from core.funcs import download_label_2, email_label, log_shipment, print_label, update_commence
from gui.address_gui import AddressGui
from gui.main_gui import MainGui, get_date_label, get_service_string
from gui.tracking_gui import TrackingGui
from shipper.addresser import address_from_bestmatch, address_from_gui, address_from_logic
from shipper.sender_receiver import recip_from_contact_address, recip_from_contact_and_key, sender_from_contact_address, \
    sender_from_address_id
from shipper.shipment import Shipment

dotenv.load_dotenv()
logger = get_amdesp_logger()
LIMITED_SHIPMENTS = 1


class Shipper:
    def __init__(self, config: Config, client: DespatchBaySDK, gui: MainGui, shipments: [Shipment],
                 shipments_dict: dict[str | Shipment]):
        self.shipments_dict = shipments_dict
        self.shipment_to_edit: Optional[Shipment] = None
        self.gui = gui
        self.config = config
        self.shipments: [Shipment] = shipments
        self.client = client

    def dispatch(self):
        self.address_shipments(outbound=self.config.outbound)
        self.gather_dbay_objs()
        booked_shipments = self.dispatch_loop()
        self.gui.post_book(shipments=booked_shipments)

    def dispatch_outbound_dropoffs(self):
        self.address_outbound_dropoffs()
        self.gather_dbay_objs()
        booked_shipments = self.dispatch_loop()
        self.gui.post_book(shipments=booked_shipments)

    def track(self):
        for shipment in self.shipments:
            if ship_ids := [shipment.outbound_id, shipment.inbound_id]:
                try:
                    self.tracking_loop(ship_ids=ship_ids)
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

    def dispatch_loop(self):
        """ pysimplegui main_loop, takes a prebuilt window and shipment list,
        listens for user input and updates shipments
        listens for go_ship  button to start booking"""
        logger.info('GUI LOOP')

        self.gui.window = self.gui.bulk_shipper_window(shipments=self.shipments)

        while True:
            self.gui.event, self.gui.values = self.gui.window.read()
            if self.gui.event == sg.WIN_CLOSED:
                self.gui.window.close()
                sys.exit()
            elif self.gui.event == '-GO_SHIP-':
                if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                    sg.popup_quick_message('Please Wait')
                    self.gui.window.close()
                    return self.process_shipments()
            else:
                s_to_e = next((shipment for shipment in self.shipments if
                               shipment.shipment_name_printable.lower() in self.gui.event.lower()))
                self.edit_shipment(shipment_to_edit=s_to_e)

    def tracking_loop(self, ship_ids):
        for shipment_id in ship_ids:
            shipment_return = self.client.get_shipment(shipment_id).is_delivered
            tracking_gui = TrackingGui(outbound=self.config.outbound, sandbox=self.config.sandbox)


    def address_outbound_dropoffs(self):
        home_sender = sender_from_address_id(address_id=self.config.home_address.dropoff_sender_id, client=self.client)
        for shipment in self.shipments:
            shipment.remote_contact = Contact(email=shipment.email, telephone=shipment.telephone,
                                              name=shipment.contact_name)
            shipment.sender = home_sender
            remote_address = self.remote_address_script(shipment=shipment)
            shipment.recipient = recip_from_contact_address(client=self.client, contact=shipment.remote_contact, address=remote_address)

    def address_shipments(self, outbound: bool):
        if self.config.home_contact and self.config.home_address.dbay_key:
            home_recipient = recip_from_contact_and_key(client=self.client, dbay_key=self.config.home_address.dbay_key,
                                                        contact=self.config.home_contact)
        else:
            raise ValueError("Home Contact or Dbay Key Missing")
        home_sender = self.client.sender(address_id=self.config.home_address.address_id)

        for shipment in self.shipments:
            shipment.remote_contact = Contact(email=shipment.email, telephone=shipment.telephone,
                                              name=shipment.contact_name)
            shipment.remote_address = self.remote_address_script(shipment=shipment)

            if outbound:
                shipment.sender = home_sender
                shipment.recipient = recip_from_contact_address(client=self.client, contact=shipment.remote_contact,
                                                                address=shipment.remote_address)

            elif not outbound:
                shipment.recipient = home_recipient
                shipment.sender = sender_from_contact_address(contact=shipment.remote_contact, client=self.client,
                                                              remote_address=shipment.remote_address)

    def remote_address_script(self, shipment):

        address = address_from_logic(client=self.client, shipment=shipment, sandbox=self.config.sandbox)
        if address is None:
            address = address_from_bestmatch(client=self.client, shipment=shipment)
        if address is None:
            address = address_from_gui(client=self.client, outbound=self.config.outbound, sandbox=self.config.sandbox,
                                       shipment=shipment)
        return address

    def gather_dbay_objs(self):
        config = self.config
        for shipment in self.shipments:
            shipment.service = self.client.get_services()[0]  # needed to get dates
            shipment.collection_date = self.get_collection_date(shipment=shipment)
            if str(shipment.send_out_date) != shipment.collection_date.date:
                if shipment.send_out_date == datetime.today().date() and datetime.now().hour >= 12:
                    sg.popup_ok("Can't Ship Today until dbay configure it")
                    # shipment.sender = get_dropoff_sender(client=self.client,
                    #                                  dropoff_sender_id=self.config.home_address.dropoff_sender_id)

            shipment.parcels = self.get_parcels(num_parcels=shipment.boxes, contents=config.parcel_contents)
            shipment.shipment_request = get_shipment_request(client=self.client, shipment=shipment)
            shipment.available_services = self.client.get_available_services(shipment.shipment_request)
            shipment.service = get_actual_service(default_service_id=config.default_shipping_service.service,
                                                  available_services=shipment.available_services)

    def gather_dbay_objs_single(self, shipment, default_service_id, parcel_contents):
        shipment.service = self.client.get_services()[0]  # needed to get dates
        shipment.collection_date = self.get_collection_date(shipment=shipment)
        shipment.parcels = self.get_parcels(num_parcels=shipment.boxes, contents=parcel_contents)
        shipment.shipment_request = get_shipment_request(client=self.client, shipment=shipment)
        shipment.available_services = self.client.get_available_services(shipment.shipment_request)
        shipment.service = get_actual_service(default_service_id=default_service_id,
                                              available_services=shipment.available_services)

    def edit_shipment(self, shipment_to_edit):
        self.shipment_to_edit = shipment_to_edit
        if 'boxes' in self.gui.event.lower():
            self.boxes_click()
        elif 'service' in self.gui.event.lower():
            self.service_click()
        elif 'date' in self.gui.event.lower():
            self.date_click()
        elif 'sender' in self.gui.event.lower():
            self.sender_click()
        elif 'recipient' in self.gui.event.lower():
            self.recipient_click()
        elif 'remove' in self.gui.event.lower():
            self.remove_click(shipment_to_remove=shipment_to_edit)

    def boxes_click(self):
        shipment_to_edit = self.shipment_to_edit
        event = self.gui.event
        window = self.gui.window
        if new_parcels := self.get_new_parcels(location=window.mouse_location()):
            shipment_to_edit.parcels = new_parcels
            window[event].update(len(shipment_to_edit.parcels))
            window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
                f'{shipment_to_edit.service.name} \n£{len(new_parcels) * shipment_to_edit.service.cost:.2f}')

    def remove_click(self, shipment_to_remove):
        # [s for s in self.shipments if s.shipment_name_printable != shipment_to_remove.shipment_name_printable]
        self.shipments = [s for s in self.shipments if s != shipment_to_remove]
        self.gui.window.close()
        self.gui.window = self.gui.bulk_shipper_window(shipments=self.shipments)

    def date_click(self):
        new_collection_date = self.gui.new_date_selector(shipment=self.shipment_to_edit,
                                                         location=self.gui.window.mouse_location())
        self.gui.window[self.gui.event].update(get_date_label(collection_date=new_collection_date))
        self.shipment_to_edit.collection_date = new_collection_date

    def sender_click(self):
        send = self.shipment_to_edit.sender
        contact = Contact(name=send.name, email=send.email, telephone=send.telephone)
        self.sr_click(s_or_r='sender', contact=contact)

    def recipient_click(self):
        rec = self.shipment_to_edit.recipient
        contact = Contact(name=rec.name, email=rec.email, telephone=rec.telephone)
        self.sr_click(s_or_r='recipient', contact=contact)

    def sr_click(self, s_or_r, contact):
        # contact = self.config.home_contact if self.config.outbound else self.shipment_to_edit.remote_contact
        if s_or_r == 'sender':
            address_to_edit = self.shipment_to_edit.sender.sender_address
        elif s_or_r == 'recipient':
            address_to_edit = self.shipment_to_edit.recipient.recipient_address
        else:
            raise ValueError('s_or_r must be sender or recipient')

        address_window = AddressGui(outbound=self.config.outbound, sandbox=self.config.sandbox, client=self.client,
                                    shipment=self.shipment_to_edit,
                                    contact=contact, address=address_to_edit)
        if new_address := address_window.get_address():
            address_to_edit = new_address
            self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=address_to_edit))

    def service_click(self):
        shipment_to_edit = self.shipment_to_edit
        if new_service := self.gui.new_service_selector(default_service=shipment_to_edit.service.name,
                                                        menu_map=get_service_menu_map(
                                                            shipment_to_edit.available_services),
                                                        location=self.gui.window.mouse_location()):
            shipment_to_edit.service = new_service
            self.gui.window[self.gui.event].update(get_service_string(service=new_service,
                                                                      num_boxes=len(shipment_to_edit.parcels)))

    def get_new_parcels(self, location) -> List[Parcel] | None:
        window = self.gui.get_new_parcels_window(location=location)
        e, v = window.read()
        if e == sg.WIN_CLOSED:
            window.close()
            return None
        if e == 'BOX':
            new_boxes = int(v[e])
            window.close()
            return self.get_parcels(new_boxes, contents=self.config.parcel_contents)

    def book_a_shipment(self, shipment: Shipment, shipment_id):
        outbound = self.config.outbound
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"

        print_email = self.gui.values.get(f'-{shipment.shipment_name_printable}_print_email-'.upper())

        setattr(shipment, f'{"outbound_id" if outbound else "inbound_id"}', shipment_id)

        shipment.shipment_return = self.client.book_shipments(shipment_id)[0]
        shipment.label_location = download_label_2(client=self.client, label_folder_path=self.config.paths.labels,
                                                   label_text=shipment.shipment_name_printable,
                                                   shipment_return=shipment.shipment_return)
        shipment.collection = self.client.get_collection(shipment.shipment_return.collection_id)

        if outbound and print_email:
            print_label(shipment=shipment)
        else:
            if not outbound and print_email:
                email_label(shipment=shipment,
                            body=self.config.return_label_email_body,
                            collection_date=shipment.collection.date.date,
                            collection_address=shipment.collection.sender_address.sender_address
                            )
        update_commence(shipment=shipment, id_to_pass=shipment_id, outbound=self.config.outbound,
                        ps_script=self.config.paths.cmc_logger)
        return shipment

    def process_shipments(self):
        config = self.config
        client = self.client
        added_shipments = []
        booked_shipments = []

        for shipment in self.shipments:
            book = self.gui.values.get(f'-{shipment.shipment_name_printable}_BOOK-'.upper())

            # dropoff = self.gui.values.get(f'-{shipment.shipment_name_printable}_DROP-'.upper())
            # if dropoff:
            #     logger.info('Converting to Dropoff')
            #     shipment.sender = sender_from_address_id(client=client,
            #                                              address_id=config.home_address.dropoff_sender_id)

            shipment.shipment_request = get_shipment_request(client=self.client, shipment=shipment)
            shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
            shipment_id = self.client.add_shipment(shipment.shipment_request)

            if book:
                try:
                    booked_shipments.append(
                        self.book_a_shipment(shipment=shipment, shipment_id=shipment_id))

                except ApiException as e:
                    sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\nAvailable balance = "
                                   f"£{client.get_account_balance().available}\n{e}\n")
                    continue
                except Exception as e:
                    logger.exception(e)
                    continue

            log_shipment(log_path=config.paths.log_json, shipment=shipment)

        return booked_shipments if booked_shipments else None

    # def post_book(self, shipments: [Shipment]):
    #     headers = []
    #     frame = self.gui.booked_shipments_frame(shipments=shipments)
    #     window2 = sg.Window('Booking Results:', layout=[[frame]])
    #     while True:
    #         e2, v2 = window2.read()
    #         if e2 in [sg.WIN_CLOSED, 'Exit']:
    #             window2.close()
    #
    #         window2.close()
    #         break


    def get_dropoff_date(self):
        pass


    def get_collection_date(self, shipment: Shipment) -> CollectionDate:
        """ return despatchbay CollecitonDate Entity
        make a menu_map of displayable dates to colleciton_date objects to populate gui choosers"""
        available_dates = self.client.get_available_collection_dates(sender_address=shipment.sender,
                                                                     courier_id=self.config.default_shipping_service.courier)
        collection_date = None

        for potential_collection_date in available_dates:
            real_date = datetime.strptime(potential_collection_date.date, DateTimeMasks.DB.value).date()
            display_date = real_date.strftime(DateTimeMasks.DISPLAY.value)
            shipment.date_menu_map.update({display_date: potential_collection_date})
            if real_date == shipment.send_out_date:
                collection_date = potential_collection_date
                shipment.date_matched = True

        collection_date = collection_date or available_dates[0]

        logger.info(
            f'PREPPING SHIPMENT - COLLECTION DATE {collection_date.date}{" - DATE MATCHED" if shipment.date_matched else ""}')
        return collection_date

    def get_parcels(self, num_parcels: int, contents: str) -> list[Parcel]:
        """ return an array of dbay parcel objects equal to the number of boxes provided
            uses arbitrary sizes because dbay api wont allow skipping even though website does"""
        parcels = []
        for x in range(num_parcels):
            parcel = self.client.parcel(
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

    def convert_to_dropoff(self, shipment):
        # self.config.home_address.dropoff_sender_id
        shipment.sender = self.client.sender()
        pass


def get_service_menu_map(available_services: List[Service]):
    return ({service.name: service for service in available_services})


def get_actual_service(default_service_id: str, available_services: [Service]) -> Service:
    return next((service for service in available_services if service.service_id == default_service_id),
                available_services[0])


# Dbay sender / recipient object getters


def get_shipment_request(client: DespatchBaySDK, shipment: Shipment):
    """ returns a dbay shipment request object from shipment"""
    request = client.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer_safe_print,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )

    logger.info(f'PREPPING SHIPMENT - SHIPMENT REQUEST {request}')
    return request


def book_shipment(client: DespatchBaySDK, shipment_id: str):
    shipment_return = client.book_shipments(shipment_id)[0]
    # shipment.collection_booked = True
    return shipment_return
