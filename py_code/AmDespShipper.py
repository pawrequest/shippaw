import xml.etree.ElementTree as ET
from dataclasses import dataclass

from dbfread import DBF

from .gui_layouts import GuiLayout
import PySimpleGUI as sg
import inspect
import json
import os
import pathlib
import re
import subprocess
import sys
import tomllib
from sys import exit
from datetime import datetime, date
from pprint import pprint
from dateutil.parser import parse

from py_code.despatchbay.despatchbay_sdk import DespatchBaySDK
from py_code.utils_pss.utils_pss import Utility

import dotenv

dotenv.load_dotenv()

DEBUG = False

LINE = f"{'-' * 130}"
TABBER = "\t\t"


# DT_DISPLAY = '%A - %B %#d'
# DT_HIRE = '%d/%m/%Y'
# DT_DB = '%Y-%m-%d'


# SANDBOX_SHIPMENT_ID = '100786-5633'
# SHIPMENT_ID = '100786-20850029'


class App:
    """
    controller for prepare_shipment and process_shipment
    """

    def __init__(self, sandbox=False):  # creat app-obj
        # create config object
        # self.sandbox = sandbox
        self.config = Config()
        self.sandbox = sandbox
        self.client = self.config.get_client(sandbox=sandbox)

    def run(self, mode, xml_file):
        self.mode = mode
        # self.xml = xml_file
        # self.shipment = Shipment(self)
        self.bulk = self.get_bulk_dbase()
        for shipment in self.bulk:
            self.shipment = shipment
            gui = Gui(self)
            self.gui = gui

            match mode:
                case 'ship_out':
                    gui.gui_ship('out')
                    sg.popup("COMPLETE")
                case 'ship_in':
                    gui.gui_ship('in')
                    sg.popup("COMPLETE")
                case 'track_out':
                    try:
                        gui.layouts.tracking_viewer_window(self.shipment.outbound_id)
                    except:
                        sg.popup_error("No Shipment ID")
                case 'track_in':
                    try:
                        gui.layouts.tracking_viewer_window(self.shipment.inbound_id)
                    except:
                        sg.popup_error("No Shipment ID")

    def get_bulk_dbase(self):
        datapath = self.config.paths['dbase_import']
        bulk_dbase = DBF(datapath)
        dbase_records = []
        for single_record in (bulk_dbase.records):
            obj = Shipment(self, single_record)
            dbase_records.append(obj)
        return dbase_records

    def get_sender_recip(self):
        shipment = self.shipment
        client = self.client

        # shipment is a return so recipient is homebase
        if shipment.is_return:
            recipient = shipment.home_recipient
            try:
                sender_address = client.find_address(shipment.postcode, shipment.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                sender_address = self.gui.address_chooser(candidates)
            sender = client.sender(name=shipment.name, email=shipment.email,
                                   telephone=shipment.telephone, sender_address=sender_address)

        # not a return so we are sender
        if not shipment.is_return:
            sender = shipment.home_sender
            try:
                recipient_address = client.find_address(shipment.postcode, shipment.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                recipient_address = self.gui.address_chooser(candidates)
            recipient = client.recipient(name=shipment.name, email=shipment.email,
                                         telephone=shipment.telephone, recipient_address=recipient_address)

            shipment.sender, shipment.recipient = sender, recipient

        return sender, recipient


class Gui:
    def __init__(self, app):
        self.client = app.client
        self.config = app.config
        self.shipment = app.shipment
        self.app = app

        self.layouts = GuiLayout(self)

    def gui_ship(self, mode, theme=None):

        match mode:
            case 'out':
                self.shipment.is_return = False
            case 'in':
                self.shipment.is_return = True
            case _:
                sg.popup_error("WRONG MODE")

        window = self.layouts.main_window()
        self.window = window
        self.populate_window()

        if self.app.sandbox:
            self.theme = sg.theme('Tan')
        else:
            sg.theme('Dark Blue')
        if theme:
            sg.theme(theme)

        while True:
            if not window:
                break
            event, values = window.read()
            window['-SENDER_POSTAL_CODE-'].bind("<Return>", "_Enter")
            window['-RECIPIENT_POSTAL_CODE-'].bind("<Return>", "_Enter")

            self.event, self.values = event, values
            shipment = self.shipment
            pprint(f'{event}  -  {[values.items()]}')
            if not self.shipment.shipment_request:
                self.shipment.shipment_request = self.make_request()

            if event in (sg.WINDOW_CLOSED, 'Exit'):
                break

            elif event == "Set Theme":
                print("[LOG] Clicked Set Theme!")
                theme_chosen = values['-THEME LISTBOX-'][0]
                print("[LOG] User Chose Theme: " + str(theme_chosen))
                window.close()
                self.gui_ship(mode='out', theme=theme_chosen)

            if event == '-DATE-':
                window['-DATE-'].update({'background_color': 'red'})

            # click company name to copy customer in
            if 'company_name' in event:
                window[event.upper()].update(self.shipment.customer)
                # window[event.upper()].refresh()

            # click 'postcode' or Return in postcode box to get address to choose from and update shipment
            if 'postal_code' in event.lower():
                self.new_address_from_postcode()

            if event == '-INBOUND_ID-':
                self.layouts.tracking_viewer_window(shipment.inbound_id)
            if event == '-OUTBOUND_ID-':
                self.layouts.tracking_viewer_window(shipment.outbound_id)

            if event == '-GO-':
                decision = values['-QUEUE OR BOOK-'].lower()
                if 'queue' or 'book' in decision:
                    shipment_request = self.make_request()
                    answer = sg.popup_scrolled(f"{decision}?\n{shipment_request}", size=(30, 30))

                    if answer == 'OK':
                        if not self.app.sandbox:
                            if not sg.popup("NOT SANDBOX DO YOU WANT TO PAY?!!!") == 'Yes':
                                continue
                        shipment_id = self.queue_shipment(shipment_request)
                        if 'book' in decision:
                            shipment_return = self.book_collection(shipment_id)
                            sg.popup(f"Collection for {self.shipment.shipment_name} booked")
                        if 'print' in decision:
                            self.print_label()
                        if 'email' in decision:
                            ...
                        self.update_commence()
                        self.log_shipment()
                        break

        window.close()

    def populate_window(self):
        window = self.window
        sender, recipient = self.app.get_sender_recip()
        for field in self.config.address_fields:
            try:
                window[f'-SENDER_{field.upper()}-'].update(getattr(sender.sender_address.sender_address, field))
                window[f'-RECIPIENT_{field.upper()}-'].update(getattr(recipient.recipient_address, field))
            except Exception as e:
                ...

        adict = {'sender': sender, 'recipient': recipient}

        for name, obj in adict.items():
            for field in self.config.contact_fields:
                value = getattr(obj, field, None)
                if value is None:
                    value = sg.popup_get_text(f"{field} Missing from {name} record- please enter:")
                    setattr(obj, field, value)
                window[f'-{name.upper()}_{field.upper()}-'].update(value)

    def new_address_from_postcode(self):
        """ click 'postcode' label, or press Return in postcode input to call.
            parses sender vs recipient from event code.
            takes postcode from window, gets list of candidate addresses with given postcode
            popup a chooser,
            """
        event, values, shipment, window = self.event, self.values, self.shipment, self.window
        postcode = None
        mode = None
        if 'sender' in event.lower():
            mode = 'sender'
            postcode = values['-SENDER_POSTAL_CODE-']
        elif 'recipient' in event.lower():
            mode = 'recipient'
            postcode = values['-RECIPIENT_POSTAL_CODE-']

        address_dict={}
        try:
            candidates = self.get_address_candidates(postcode=postcode)
            chosen_address = self.address_chooser(candidates)
            address_dict = {k: v for k, v in vars(chosen_address).items() if 'soap' not in k}
            address_dict.pop('country_code', None)

            if mode == 'sender':
                shipment.sender.sender_address = chosen_address
            elif mode == 'recipient':
                shipment.recipient.recipient_address = chosen_address

            for k, v in address_dict.items():
                window[f'-{mode.upper()}_{k.upper()}-'].update(v if v else '')
        except:
            pass

    def make_request(self):
        values, shipment, client = self.values, self.shipment, self.client
        shipment.parcels = self.layouts.get_parcels(values['-BOXES-'])
        shipment.date = self.layouts.date_menu_map.get(values['-DATE-'])
        shipment.service = self.layouts.service_menu_map.get(values['-SERVICE-'])

        shipment_request = client.shipment_request(
            service_id=shipment.service.service_id,
            parcels=shipment.parcels,
            client_reference=shipment.name,
            collection_date=shipment.date,
            sender_address=shipment.sender,
            recipient_address=shipment.recipient,
            follow_shipment=True
        )
        return shipment_request

    def get_address_candidates(self, postcode=None):
        shipment, client = self.shipment, self.client
        if postcode is None:
            postcode = shipment.postcode

        while True:
            try:
                candidates = client.get_address_keys_by_postcode(postcode)
            except:
                if sg.popup_yes_no("Bad Postcode - Try again?") == 'Yes':
                    postcode = sg.popup_get_text("Enter Postcode")
                    continue
                else:
                    # no retry = no candidates
                    return None
            else:
                return candidates

    def address_chooser(self, candidates):
        client = self.client
        # build address option menu dict
        address_key_dict = {}
        for candidate in candidates:
            candidate_hr = candidate.address
            address_key_dict.update({candidate_hr: candidate.key})

        # deploy address option popup using dict as mapping
        address_key = self.layouts.combo_popup(address_key_dict)
        if address_key:
            address = client.get_address_by_key(address_key)
            return address

    def queue_shipment(self, shipment_request):
        shipment = self.shipment
        client = self.client
        if shipment.is_return:
            shipment.inbound_id = client.add_shipment(shipment_request)
            shipment_id = shipment.inbound_id
        else:
            shipment.outbound_id = client.add_shipment(shipment_request)
            shipment_id = shipment.outbound_id
        return shipment_id

    def book_collection(self, shipment_id):
        shipment = self.shipment
        client = self.client
        try:
            shipment_return = client.book_shipments(shipment_id)[0]  # debug there could be more than one here??
            sg.popup_scrolled(f'Shipment booked: \n{shipment_return}', size=(30, 30))
            shipment.collection_booked = True
        except:
            sg.popup_error("Unable to Book")
            return None
        else:
            # save label
            try:
                label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
                label_string = shipment.shipment_name.replace(r'/', '-') + '.pdf'
                shipment.label_location = self.config.label_path / label_string
                label_pdf.download(shipment.label_location)
            except:
                sg.popup_error("Label not downloaded")
            shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
            return shipment_return

    def print_label(self):
        try:
            os.startfile(str(self.shipment.label_location), "print")
        except Exception as e:
            sg.popup_error(f"\n ERROR: Unable to print \n{e}")
        else:
            self.printed = True

    def update_commence(self):
        """
                runs cmclibnet via powershell script to add tracking numbes to commence db

                :return:
                """

        class CommenceEditError(Exception):
            pass

        ps_script = str(self.config.paths['cmc_log'])
        try:  # utility class static method runs powershell script bypassing execuction policy
            ship_id_to_pass = str(
                self.shipment.inbound_id if self.shipment.is_return else self.shipment.outbound_id)
            commence_edit = Utility.powershell_runner(ps_script, self.shipment.category, self.shipment.shipment_name,
                                                      ship_id_to_pass,
                                                      str(self.shipment.is_return), 'debug')

            if commence_edit == 1:
                raise CommenceEditError("\nERROR: Commence Tracking not updated - is Commence running?")

        except CommenceEditError as e:
            ...
            # sg.popup_error(f"{e}")

        except FileNotFoundError as e:
            ...
            # sg.popup(f"ERROR: Unable to log tracking to Commence - FileNotFoundError : {e.filename}")

        except Exception as e:
            ...
            # sg.popup(f"{e=} \nERROR: Unable to log tracking to Commence")

        else:
            ...
            # sg.popup("\nCommence Tracking updated")

    def log_shipment(self):
        # export from object attrs
        shipment = self.shipment
        shipment.boxes = len(self.shipment.parcels)
        export_dict = {}

        for field in self.config.export_fields:
            try:
                if field == 'sender':
                    val = shipment.sender.sender_address
                    val = f'{val.street} - {val.postal_code}'
                elif field == 'recipient':
                    val = shipment.recipient.recipient_address
                    val = f'{val.street} - {val.postal_code}'
                else:
                    val = getattr(self.shipment, field)
                    if isinstance(val, datetime):
                        val = f"{val.isoformat(sep=' ', timespec='seconds')}"

                export_dict.update({field: val})
            except Exception as e:
                print(f"{field} not found in shipment \n{e}")

        with open(self.config.paths['log'], 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",\n")
        sg.popup(f" Json exported to {self.config.paths['log']}:\n {export_dict}")

    def email_label(self):
        ...


class AmherstXml:
    def __init__(self, xml_file, config):

        # inspect xml
        tree = ET.parse(xml_file)
        root = tree.getroot()
        fields = root[0][2]
        category = root[0][0].text

        shipment_fields = config.shipment_fields
        ship_dict = dict()
        for field in fields:
            k = field[0].text
            k = self.to_snake_case(k)
            v = field[1].text
            if v:
                k = self.unsanitise(k)
                v = self.unsanitise(v)

                if "Number" in k:
                    v = v.replace(',', '')
                if k == 'name':
                    k = 'shipment_name'
                # if pattern.search(k):
                if k[:6] == "deliv ":
                    k = k.replace('deliv', 'delivery')
                k = k.replace('delivery_', '')
                if k == 'tel':
                    k = 'telephone'
                ship_dict.update({k: v})
                if k in config.shipment_fields:
                    setattr(self, k, v)

        # get customer name
        if category == "Hire":
            self.customer = root[0][3].text
        elif category == "Customer":
            self.customer = fields[0][1].text
            self.shipment_name = f'{self.shipment_name} - {datetime.now().isoformat(" ", timespec="seconds")}'
        elif category == "Sale":
            self.customer = root[0][3].text

        # convert to date object
        if self.send_out_date:
            # noinspection PyTypeChecker
            self.send_out_date = parse(self.send_out_date)
        else:
            self.send_out_date = datetime.today()

        self.category = category
        self.ship_dict = ship_dict
        # noinspection PyTypeChecker
        self.search_term = self.parse_amherst_address_string(self.address)

        missing = []
        for attr_name in shipment_fields:
            if attr_name not in vars(self):
                if attr_name not in ['delivery_cost', 'inbound_id', 'outbound_id']:
                    missing.append(attr_name)
        if missing:
            print_and_pop(f"*** Warning - {missing} not found in ship_dict - Warning ***")

    def to_snake_case(self, input_string):
        """Convert a string to lowercase snake case."""
        input_string = input_string.replace(" ", "_")
        input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
        input_string = input_string.lower()
        return input_string

    def parse_amherst_address_string(self, str_address):
        firstline = str_address.strip().split("\n")[0]
        first_block = (str_address.split(" ")[0]).split(",")[0]
        first_char = first_block[0]
        for char in firstline:
            if not char.isalnum() and char != " ":
                firstline = firstline.replace(char, "")

        if first_char.isnumeric():
            return first_block
        else:
            return firstline

    def unsanitise(self, input_string):
        """ deals with special and escape chars"""
        input_string = input_string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;",
                                                                                                 chr(39)).replace(
            "&lt;",
            chr(60)).replace(
            "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
        return input_string


# noinspection PyUnresolvedReferences
class Config:
    """
    sets up the environment
    creates a dbay client
    """

    def __init__(self):
        # get config from toml
        self.root_dir = pathlib.Path(pathlib.Path(__file__)).parent.parent
        config_path = self.root_dir / 'config.toml'
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        for k, v in config.items():
            setattr(self, k, v)

        self.paths = config['paths']
        cmc_dll = pathlib.Path
        self.label_path = pathlib.Path(self.root_dir / self.paths['labels'])
        self.label_path.mkdir(parents=True, exist_ok=True)
        self.home_sender_id = config['home_address']['address_id']

        # commence setup
        if not pathlib.Path(self.paths['cmc_dll']).exists():
            sg.popup_error(f"Vovin CmCLibNet is not installed in expected location {cmc_dll}")
            print(f"Vovin CmCLibNet is not installed in expected location {cmc_dll}")
            self.install_cmc()

        if DEBUG:
            print_and_long_pop(f"{self.root_dir=} -- {config=} \n \n {self}")
            # dbay client setup

    def get_client(self, sandbox=True):
        # parse shipmode argument and setup API keys from .env

        if sandbox:
            print(f"\n {TABBER * 2}*** !!! SANDBOX MODE !!! *** \n")
            api_user = os.getenv(self.dbay_sand['api_user'])
            api_key = os.getenv(self.dbay_sand['api_key'])
            self.courier_id = self.dbay_sand['courier']
            self.service_id = self.dbay_sand['service']
        else:
            api_user = os.getenv(self.dbay_prod['api_user'])
            api_key = os.getenv(self.dbay_prod['api_key'])
            self.courier_id = self.dbay_prod['courier']
            self.service_id = self.dbay_prod['service']

        client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        return client

    def install_cmc(self):
        try:
            subprocess.run([str(self.paths['cmc_inst']), '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           check=True)
        except subprocess.CalledProcessError as e:
            print_and_pop(f"\n\nERROR: CmcLibNet Installer Failed - logging to commence is impossible \n {e}")


def debug_msg(e=None):
    debug_msg = "\n\n"
    debug_msg += f"\nCurrent method = {inspect.currentframe().f_back.f_code.co_name}\n"
    if e:
        debug_msg += f"ERROR: {e}" if {e} else None


def print_and_pop(print_text: str):
    sg.popup(print_text)
    print(print_text)


def print_and_long_pop(print_string: str):
    sg.popup_scrolled(print_string)
    pprint(print_string)


class Amherst_one_dbase:
    def __init__(self, data, is_return=False):
        self.shipment_name = data['NAME'].split('\x00')[0]
        self.date = data['SEND_OUT_D']
        self.address = data['DELIVERY_A'].split('\x00')[0]
        self.name = data['DELIVERY_C'].split('\x00')[0]  # contact
        self.company_name = data['DELIVERY_N'].split('\x00')[0]
        self.postcode = data['DELIVERY_P'].split('\x00')[0]
        self.boxes = data['BOXES']
        self.status = data['STATUS']
        self.email = data['DELIVERY_E'].split('\x00')[0]
        self.telephone = data['DELIVERY_T'].split('\x00')[0]
        self.customer = data['FIELD17'].split('\x00')[0]
        self.is_return = is_return
        try:
            self.id_inbound = data['ID_INBOUND']
            self.id_outbound = data['ID_OUTBOUND']
        except:
            ...
        self.service = None
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = False


class Shipment(Amherst_one_dbase):
    def __init__(self, app, single_dbase, is_return=False):
        """
        :param ship_dict: a dictionary of shipment details
        :param config: a config() object
        :param reference:
        :param label_text:
        """
        super().__init__(single_dbase)
        # xml_file = app.xml
        # attrs from importer class
        # super().__init__(xml_file, config)

        config = app.config
        client = app.client

        self.home_sender = client.sender(
            address_id=config.home_sender_id,
            name=config.home_address['contact'],
            email=config.home_address['email'],
            telephone=config.home_address['telephone'],
            sender_address=client.get_sender_addresses()[0]
        )
        self.home_recipient = client.recipient(
            name=config.home_address['contact'],
            email=config.home_address['email'],
            telephone=config.home_address['telephone'],
            recipient_address=client.find_address(config.home_address['postal_code'],
                                                  config.home_address['search_term'])

        )
        self.available_dates = client.get_available_collection_dates(self.home_sender, config.courier_id)  # get dates

        if DEBUG:
            pprint(f"\n{self=}\n")
