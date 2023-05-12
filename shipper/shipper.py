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
from core.funcs import print_label, log_shipment, email_label, download_label, update_commence, \
    check_today_ship
from shipper.shipment import Shipment

from shipper.sender_receiver import get_sender_recip, get_home_sender, get_home_recipient
from gui.address_gui import AddressGui
from gui.main_gui import MainGui
from gui.tracking_gui import tracking_loop

dotenv.load_dotenv()
logger = get_amdesp_logger()
LIMITED_SHIPMENTS = 1


class Shipper:
    def __init__(self, config: Config, client: DespatchBaySDK, gui: MainGui, shipments: [Shipment]):
        self.shipment_to_edit: Optional[Shipment] = None
        self.gui = gui
        self.config = config
        self.shipments: [Shipment] = shipments
        self.client = client

    def dispatch(self):
        mode = self.config.mode
        try:
            if 'ship' in mode.lower():
                prepped_shipments = self.prep_shipments()
                booked_shipments = self.main_gui_loop(prepped_shipments)
                self.gui.post_book(shipments=booked_shipments)

            elif 'track' in mode.lower():
                for shipment in self.shipments:
                    if any([shipment.outbound_id, shipment.inbound_id]):
                        result = tracking_loop(self.gui, shipment=shipment)
            else:
                raise ValueError('Ship Mode Fault')
        except Exception as e:
            logger.exception(f'DISPATCH EXCEPTION \n{e}')

        if sg.popup_yes_no("Restart? No to close") == 'Yes':
            self.dispatch()
        else:
            sys.exit()

    def prep_shipments(self):
        """  gets sender, recipient, service, date, parcels and shipment request objects from dbay api \n
        stores all in shipment attrs
        uses an arbitrary service to get collection dates, then gets real service from eventual shipment_return dbay object"""
        logger.info('PREP SHIPMENTS')
        prepped_shipments = []
        config = self.config
        client = self.client

        # get a dbay object representing home base for either sender or receiver as per config.outbound
        home_sender_recip = (get_home_sender(client=client, config=config) if config.outbound
                             else get_home_recipient(client=client, config=config))
        logger.info(f'PREP SHIPMENT -  {home_sender_recip=}')

        for shipment in self.shipments:
            try:
                shipment.remote_contact = Contact(email=shipment.email, telephone=shipment.telephone,
                                                  name=shipment.contact_name)
                get_sender_recip(self.client, self.config, home_sender_recip=home_sender_recip, shipment=shipment)
                shipment.service = client.get_services()[0]  # needed to get dates
                if check_today_ship(shipment) is None:  # no bookings after 1pm
                    continue
                shipment.collection_date = self.get_collection_date(shipment=shipment)
                shipment.parcels = self.get_parcels(num_parcels=shipment.boxes, contents=config.parcel_contents)
                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
                shipment.available_services = client.get_available_services(shipment.shipment_request)
                shipment.service = get_actual_service(default_service_id=config.default_shipping_service.service,
                                                      available_services=shipment.available_services)

                prepped_shipments.append(shipment)

            except Exception as e:
                self.shipments.remove(shipment)
                logger.exception(f'Error with {shipment.shipment_name_printable}:\n {e}')
                continue

        return prepped_shipments

    def main_gui_loop(self, shipments: [Shipment]):
        """ pysimplegui main_loop, takes a prebuilt window and shipment list,
        listens for user input and updates shipments
        listens for go_ship  button to start booking"""
        logger.info('GUI LOOP')

        self.gui.window = self.gui.bulk_shipper_window(shipments=shipments)

        while True:
            self.gui.event, self.gui.values = self.gui.window.read()
            if self.gui.event == sg.WIN_CLOSED:
                self.gui.window.close()
                sys.exit()
            elif self.gui.event == '-GO_SHIP-':
                if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                    sg.popup_quick_message('Please Wait')
                    self.gui.window.close()
                    return self.queue_and_book()
            else:
                self.edit_shipment(shipments=shipments)

    # def do_jobs(self):
    #     job = Job()

    def edit_shipment(self, shipments):
        self.shipment_to_edit: Shipment = next((shipment for shipment in shipments
                                                if shipment.shipment_name_printable.lower() in self.gui.event.lower()))
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
            shipments, self.gui.window = self.remove_click(shipments=shipments)

    def boxes_click(self):
        shipment_to_edit = self.shipment_to_edit
        event = self.gui.event
        window = self.gui.window
        if new_parcels := self.get_new_parcels(location=window.mouse_location()):
            shipment_to_edit.parcels = new_parcels
            window[event].update(len(shipment_to_edit.parcels))
            window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
                f'{shipment_to_edit.service.name} \n£{len(new_parcels) * shipment_to_edit.service.cost:.2f}')

    def remove_click(self, shipments: [Shipment]):
        shipments = [s for s in shipments if s != self.shipment_to_edit]
        self.gui.window.close()
        window = self.gui.bulk_shipper_window(shipments=shipments)
        return shipments, window

    def recipient_click(self):
        contact = self.shipment_to_edit.remote_contact if self.config.outbound else self.config.home_contact
        old_address = self.shipment_to_edit.recipient.recipient_address
        address_window = AddressGui(config=self.config, client=self.client, shipment=self.shipment_to_edit,
                                    address=old_address, contact=contact)
        if new_address := address_window.get_address():
            self.shipment_to_edit.recipient.recipient_address = new_address
            self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=new_address))

    def date_click(self):
        new_collection_date = self.gui.new_date_selector(shipment=self.shipment_to_edit,
                                                         location=self.gui.window.mouse_location())
        self.gui.window[self.gui.event].update(self.gui.get_date_label(collection_date=new_collection_date))
        self.shipment_to_edit.collection_date = new_collection_date

    def sender_click(self):
        contact = self.config.home_contact if self.config.outbound else self.shipment_to_edit.remote_contact
        old_address = self.shipment_to_edit.sender.sender_address

        address_window = AddressGui(config=self.config, client=self.client, shipment=self.shipment_to_edit,
                                    contact=contact, address=old_address)
        if new_address := address_window.get_address():
            self.shipment_to_edit.sender.sender_address = new_address
            self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=new_address))

    def service_click(self):
        shipment_to_edit = self.shipment_to_edit
        if new_service := self.gui.new_service_selector(default_service=shipment_to_edit.service.name,
                                                        menu_map=get_service_menu_map(
                                                            shipment_to_edit.available_services),
                                                        location=self.gui.window.mouse_location()):
            shipment_to_edit.service = new_service
            self.gui.window[self.gui.event].update(self.gui.get_service_string(service=new_service,
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

    #
    # def get_new_parcels(self, location) -> :
    #     window = self.gui.get_new_parcels_window(location=location)
    #     e, v = window.read()
    #     if e == sg.WIN_CLOSED:
    #         window.close()
    #         return None
    #     if e == 'BOX':
    #         new_boxes = v[e]
    #         window.close()
    #         return self.get_parcels(int(new_boxes), contents = self.config.parcel_contents)

    def queue_and_book(self):
        config = self.config
        client = self.client
        booked_shipments = []

        for shipment in self.shipments:
            try:
                shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
                add = True
                book = True

                if add:
                    shipment_id = client.add_shipment(shipment.shipment_request)
                    setattr(shipment, f'{"outbound_id" if config.outbound else "inbound_id"}', shipment_id)

                    if book:
                        shipment.shipment_return = book_shipment(client=client, shipment_id=shipment_id)
                        download_label(client=client, config=config, shipment=shipment)

                        if config.outbound:
                            print_label(shipment=shipment)
                        else:
                            if sg.popup_yes_no(f'Email Label to {shipment.email}?') == 'Yes':
                                email_label(recipient=shipment.email, body=config.return_label_email_body,
                                            attachment=shipment.label_location)

                        booked_shipments.append(shipment)
                    update_commence(config=config, shipment=shipment, id_to_pass=shipment_id)
                    log_shipment(config=config, shipment=shipment)
                    continue

            except ApiException as e:
                sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\n"
                               f"\nServer returned the following error:\n"
                               f"{e}\n"
                               f"\nThat probably didn't help?\n"
                               f"How about this?:\n"
                               f"Available balance = £{client.get_account_balance().available}\n")
                continue
            except Exception as e:
                logger.exception(e)

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

        logger.info(f'PREPPING SHIPMENT - COLLECTION DATE {collection_date}')
        return collection_date

    # def get_arbitrary_service(self) -> Service:
    #     """ needed to get available dates, swapped out for real service later """
    #     client = self.client
    #     config = self.config
    #     all_services: [Service] = client.get_services()
    #     arbitrary_service: Service = next(
    #         (service for service in all_services if service.service_id == config.dbay_creds.service_id),
    #         all_services[0])
    #     logger.info(f'PREP SHIPMENT - ARBITRARY SERVICE {arbitrary_service.name}')
    #
    #     return arbitrary_service

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
        logger.info(f'PREPPING SHIPMENT - PARCELS {parcels}')

        return parcels


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
        client_reference=shipment.customer,
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

# def get_dates_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
#     """ get available collection dates as dbay collection date objects for shipment.sender.address
#         construct a menu_def for a combo-box
#         if desired send-date matches an available date then select it as default, otherwise select soonest colelction
#         return a dict with values and default_value"""
#
#     # potential dates as dbay objs not proper datetime objs
#     available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.courier_id)
#     datetime_mask = config.datetime_masks.display
#
#     chosen_collection_date_dbay = next((date for date in available_dates if parse(date.date) == shipment.date),
#                                        available_dates[0])
#
#     chosen_date_hr = f'{parse(chosen_collection_date_dbay.date):{datetime_mask}}'
#     shipment.date_menu_map.update({f'{parse(date.date):{datetime_mask}}': date for date in available_dates})
#     men_def = [f'{parse(date.date):{datetime_mask}}' for date in available_dates]
#
#     shipment.date = chosen_collection_date_dbay
#     return {'default_value': chosen_date_hr, 'values': men_def}
#
