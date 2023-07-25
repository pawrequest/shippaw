
import sys
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Protocol

import PySimpleGUI as sg
import dotenv
from despatchbay.despatchbay_entities import CollectionDate, Parcel, Service, Address
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException

from core.config import Config, logger
from core.enums import Contact, DateTimeMasks
from core.funcs import download_label_2, email_label, log_shipment, print_label, update_commence
from gui.address_gui import AddressGui
from gui.main_gui import MainGui, get_date_label, get_service_string, get_address_button_string
from gui.tracking_gui import TrackingGui
from shipper.addresser import fuzzy_address, address_from_gui, address_from_direct_search, sender_from_address_id, \
    recip_from_contact_and_key, \
    sender_from_contact_address, recip_from_contact_address, get_explicit_match
from shipper.shipment import Shipment

dotenv.load_dotenv()

class GuiChoices(Enum):
    go_ship = '-GO-SHIP-'
    edit_ship = auto()


class Captain:
    def __init__(self, shipper, gui:MainGui, shipments):
        self.shipper = shipper
        self.gui = gui
        self.shipments = shipments
        self.shipment_to_edit: Shipment | None = None

    def voyage(self, outbound):
        self.shipper.address_outbound if outbound \
            else self.shipper.address_inbound()
        self.shipper.gathe
        window = self.gui.window

        while True:
            result:GuiChoices = self.dispatch_loop()

            match result:
                case GuiChoices.go_ship:
                    self.shipper.process_shipments()
                case GuiChoices.edit_ship:
                    self.shipper.shipment_to_edit = ""
                    self.shipper.edit_shipment(shipment_to_edit=self.shipment_to_edit)

            booked_shipments = self.shipper.dispatch()
            self.gui.post_book(shipments=booked_shipments)

    def dispatch_loop(self) -> GuiChoices:
        """ pysimplegui main_loop, takes a prebuilt window and shipment list,
        listens for user input to edit and update shipments
        listens for go_ship  button to start booking"""
        logger.info('GUI LOOP')
        gui = self.gui
        window = gui.main_window(shipments=self.shipments)

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                window.close()
                sys.exit()
            elif gui.event == GuiChoices.go_ship:
                if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                    sg.popup_quick_message('Please Wait')
                    gui.window.close()
                    return GuiChoices.go_ship
            else:
                shipment_to_edit = next((shipment for shipment in shipments if
                                         shipment.shipment_name_printable.lower() in gui.event.lower()))
                edit_shipment(shipment_to_edit=shipment_to_edit)


