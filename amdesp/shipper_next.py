import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import PySimpleGUI as sg
import dotenv
import win32com.client
from fuzzywuzzy import fuzz

from amdesp.address_window import AddressGui
from amdesp.config import Config
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from amdesp.enums import BestMatch, Contact, DateTimeMasks, FieldsList, FuzzyScores
from amdesp.gui import MainGui
from amdesp.shipment import Shipment
from amdesp.config import get_amdesp_logger
from amdesp.tracking_gui import tracking_loop

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
            if 'ship' in mode:
                prepped_shipments = self.prep_shipments()
                booked_shipments = self.main_gui_loop(prepped_shipments)
                self.gui.post_book(shipments=booked_shipments)

            elif 'track' in mode:
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
                    if booked_ship := self.queue_and_book():
                        self.gui.window.close()
                        return booked_ship
            else:
                self.edit_shipment(shipments=shipments)

    def edit_shipment(self, shipments):
        self.shipment_to_edit: Shipment = next((shipment for shipment in shipments
                                                if shipment.shipment_name_printable.lower() in self.gui.event.lower()))
        if 'boxes' in self.gui.event.lower():
            self.boxes_click()
        if 'service' in self.gui.event.lower():
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
        if new_boxes := self.get_new_parcels(location=window.mouse_location()):
            shipment_to_edit.parcels = new_boxes
            window[event].update(f'{len(shipment_to_edit.parcels)}')
            window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
                f'{shipment_to_edit.service.name} \n£{len(new_boxes) * shipment_to_edit.service.cost}')

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
        new_address = address_window.address_gui_loop()
        self.shipment_to_edit.recipient.recipient_address = new_address
        self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=new_address))
        ...

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
        new_address = address_window.address_gui_loop()
        if not new_address:
            return
        self.shipment_to_edit.sender.sender_address = new_address
        self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=new_address))

    def service_click(self):
        shipment_to_edit = self.shipment_to_edit
        new_service = self.gui.new_service_selector(default_service=shipment_to_edit.service.name,
                                                    menu_map=shipment_to_edit.service_menu_map,
                                                    location=self.gui.window.mouse_location())
        shipment_to_edit.service = new_service
        self.gui.window[self.gui.event].update(
            self.gui.get_service_string(service=new_service, num_boxes=len(shipment_to_edit.parcels)))

    def get_new_parcels(self, location):
        window = self.gui.get_new_parcels_window(location=location)
        e, v = window.read()
        if e == sg.WIN_CLOSED:
            window.close()
        if e == 'BOX':
            new_boxes = v[e]
            window.close()
            if parcels := self.get_parcels(int(new_boxes)):
                return parcels

    def queue_and_book(self):
        config = self.config
        client = self.client
        booked_shipments = []

        for shipment in self.shipments:
            try:
                shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)

                shipment_id = client.add_shipment(shipment.shipment_request)
                setattr(shipment, f'{"outbound_id" if config.outbound else "inbound_id"}', shipment_id)

                shipment.shipment_return = book_shipment(client=client, shipment_id=shipment_id)

                download_label(client=client, config=config, shipment=shipment)

                if config.outbound:
                    print_label(shipment=shipment)
                else:
                    if sg.popup_yes_no(f'Email Label to {shipment.email}?') == 'Yes':
                        email_label(recipient=shipment.email, body=config.return_label_email_body,
                                    attachment=shipment.label_location)

                update_commence(config=config, shipment=shipment, id_to_pass=shipment_id)
                booked_shipments.append(shipment)
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

