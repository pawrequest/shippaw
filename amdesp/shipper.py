import xml.etree.ElementTree as ET

from dbfread import DBF

import PySimpleGUI as sg
import inspect
import os
import pathlib
import subprocess
import tomllib
from datetime import datetime
from pprint import pprint
from dateutil.parser import parse

from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.gui import Gui

import dotenv

dotenv.load_dotenv()

DEBUG = False

LINE = f"{'-' * 130}"
TABBER = "\t\t"


# SANDBOX_SHIPMENT_ID = '100786-5633'
# SHIPMENT_ID = '100786-20850029'


class App:
    def __init__(self, sandbox=False):  # creat app-obj
        # create config object
        self.config = Config()
        self.sandbox = sandbox
        try:
            self.client = self.config.get_client(sandbox=sandbox)
        except Exception as e:
            print_and_pop(f"Unable to fetch DespatchBay Client due to: \n {e}")


        # todo genericise
        #
    def run(self, mode, in_file):
        self.mode = mode
        self.shipments = []
        file_ext = in_file.split('.')[-1]
        if file_ext == 'xml':
            ship_dict = self.ship_dict_from_xml(in_file)
            self.shipments.append(Shipment(app=self, ship_dict=ship_dict))
        for shipment in self.shipments:
            shipment.search_term = parse_amherst_address_string(shipment.address_as_str)
            shipment.sender, shipment.recipient = self.get_sender_recip(shipment)
            self.shipment = shipment
            ...
        
        # elif 'bulk' in mode:
        #     self.bulk = self.get_bulk_dbase()
        #     for shipment in self.bulk:
        #         self.shipments.append(shipment)
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

    def ship_dict_from_xml(self, xml_file):
        # inspect xml
        config = self.config
        shipment_fields = config.shipment_fields
        ship_dict = dict()
        tree = ET.parse(xml_file)
        root = tree.getroot()
        fields = root[0][2]


        category = root[0][0].text
        for field in fields:
            k = field[0].text
            k = to_snake_case(k)
            v = field[1].text
            if v:
                k = unsanitise(k)
                v = unsanitise(v)

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
                if k == 'all_address':
                    k = 'address_as_str'
                ship_dict.update({k: v})

        # get customer name
        if category == "Hire":
            ship_dict['customer'] = root[0][3].text
        elif category == "Customer":
            ship_dict['customer'] = fields[0][1].text
            ship_dict['shipment_name'] = f'{ship_dict["shipment_name"]} - {datetime.now().isoformat(" ", timespec="seconds")}'
        elif category == "Sale":
            ship_dict['customer'] = root[0][3].text

        # convert to date object
        ship_dict['send_out_date'] = ship_dict.get('send_out_date', None)
        if ship_dict['send_out_date']:
            ship_dict['send_out_date'] = parse(ship_dict['send_out_date'])
        else:
            ship_dict['send_out_date'] = datetime.today()

        ship_dict['category'] = category
        ship_dict['search_term'] = parse_amherst_address_string(ship_dict['address'])

        ship_dict['boxes'] = ship_dict.get('boxes', 1)

        missing = []
        for attr_name in shipment_fields:
            if attr_name not in ship_dict.keys():
                if attr_name not in ['cost', 'inbound_id', 'outbound_id']:
                    missing.append(attr_name)
        if missing:
            print_and_pop(f"*** Warning - {missing} not found in ship_dict - Warning ***")
        return ship_dict

    # def get_bulk_dbase(self):
    #     datapath = self.config.paths['dbase_import']
    #     try:
    #         bulk_dbase = DBF(datapath)
    #         dbase_records = []
    #         for single_record in (bulk_dbase.records):
    #             obj = Shipment(self, single_record)
    #             dbase_records.append(obj)
    #     except Exception as e:
    #         print_and_pop(e)
    #     else:
    #         return dbase_records

    def get_sender_recip(self, shipment):
        client = self.client

        # shipment is a return so recipient is homebase
        if shipment.is_return:
            recipient = client.get_sender_addresses()[0]
            try:
                sender_address = client.find_address(shipment.postcode, shipment.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                sender_address = self.gui.address_chooser(candidates)
            sender = client.sender(name=shipment.contact, email=shipment.email,
                                   telephone=shipment.telephone, sender_address=sender_address)

        # not a return so we are sender
        else:
            sender = client.get_sender_addresses()[0]
            try:
                recipient_address = client.find_address(shipment.postcode, shipment.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                recipient_address = self.gui.address_chooser(candidates)
            recipient = client.recipient(name=shipment.contact, email=shipment.email,
                                         telephone=shipment.telephone, recipient_address=recipient_address)

        shipment.sender, shipment.recipient = sender, recipient

        return sender, recipient


# class AmherstXml:
#     def __init__(self, xml_file, config):
#
#         # inspect xml
#         tree = ET.parse(xml_file)
#         root = tree.getroot()
#         fields = root[0][2]
#         category = root[0][0].text
#
#         shipment_fields = config.shipment_fields
#         ship_dict = dict()
#         for field in fields:
#             k = field[0].text
#             k = self.to_snake_case(k)
#             v = field[1].text
#             if v:
#                 k = self.unsanitise(k)
#                 v = self.unsanitise(v)
#
#                 if "Number" in k:
#                     v = v.replace(',', '')
#                 if k == 'name':
#                     k = 'shipment_name'
#                 # if pattern.search(k):
#                 if k[:6] == "deliv ":
#                     k = k.replace('deliv', 'delivery')
#                 k = k.replace('delivery_', '')
#                 if k == 'tel':
#                     k = 'telephone'
#                 ship_dict.update({k: v})
#                 if k in config.shipment_fields:
#                     setattr(self, k, v)
#
#         # get customer name
#         if category == "Hire":
#             self.customer = root[0][3].text
#         elif category == "Customer":
#             self.customer = fields[0][1].text
#             self.shipment_name = f'{self.shipment_name} - {datetime.now().isoformat(" ", timespec="seconds")}'
#         elif category == "Sale":
#             self.customer = root[0][3].text
#
#         # convert to date object
#         if self.send_out_date:
#             # noinspection PyTypeChecker
#             self.send_out_date = parse(self.send_out_date)
#         else:
#             self.send_out_date = datetime.today()
#
#         self.category = category
#         self.ship_dict = ship_dict
#         # noinspection PyTypeChecker
#         self.search_term = self.parse_amherst_address_string(self.address)
#
#         missing = []
#         for attr_name in shipment_fields:
#             if attr_name not in vars(self):
#                 if attr_name not in ['delivery_cost', 'inbound_id', 'outbound_id']:
#                     missing.append(attr_name)
#         if missing:
#             print_and_pop(f"*** Warning - {missing} not found in ship_dict - Warning ***")
#
#     def to_snake_case(self, input_string):
#         """Convert a string to lowercase snake case."""
#         input_string = input_string.replace(" ", "_")
#         input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
#         input_string = input_string.lower()
#         return input_string
#
#     def parse_amherst_address_string(self, str_address):
#         firstline = str_address.strip().split("\n")[0]
#         first_block = (str_address.split(" ")[0]).split(",")[0]
#         first_char = first_block[0]
#         for char in firstline:
#             if not char.isalnum() and char != " ":
#                 firstline = firstline.replace(char, "")
#
#         if first_char.isnumeric():
#             return first_block
#         else:
#             return firstline
#
#     def unsanitise(self, input_string):
#         """ deals with special and escape chars"""
#         input_string = input_string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;",
#                                                                                                  chr(39)).replace(
#             "&lt;",
#             chr(60)).replace(
#             "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
#         return input_string

def to_snake_case(input_string):
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string

def parse_amherst_address_string(str_address):
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

def unsanitise(input_string):
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
        self.shipment_fields = config['shipment_fields']

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
        except FileNotFoundError as e:
            print_and_pop(e)

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


# class Amherst_one_dbase:
#     def __init__(self, data, is_return=False):
#         self.shipment_name = data['NAME'].split('\x00')[0]
#         self.date = data['SEND_OUT_D']
#         self.address = data['DELIVERY_A'].split('\x00')[0]
#         self.name = data['DELIVERY_C'].split('\x00')[0]  # contact
#         self.company_name = data['DELIVERY_N'].split('\x00')[0]
#         self.postcode = data['DELIVERY_P'].split('\x00')[0]
#         self.boxes = data['BOXES']
#         self.status = data['STATUS']
#         self.email = data['DELIVERY_E'].split('\x00')[0]
#         # different fieldnames at home vs at work...
#         self.telephone = data['DELIVERY_T'].split('\x00')[0]
#         if data['FIELD10']:
#             self.customer = data['FIELD10'].split('\x00')[0]
#         elif data['FIELD17']:
#             self.customer = data['FIELD10'].split('\x00')[0]
#         else:
#             print("Customer fieldname is neither FIELD10 nor FIELD17 in Commence export DBase")
#         self.is_return = is_return
#         try:
#             self.inbound_id = data['ID_INBOUND']
#             self.outbound_id = data['ID_OUTBOUND']
#         except:
#             ...
#         self.service = None
#         self.sender = None
#         self.recipient = None
#         self.parcels = None
#         self.collection_booked = False


# class Shipment(Amherst_one_dbase):
#     def __init__(self, app, single_dbase, is_return=False):
#         """
#         :param ship_dict: a dictionary of shipment details
#         :param config: a config() object
#         :param reference:
#         :param label_text:
#         """
#         super().__init__(single_dbase)
#         # xml_file = app.xml
#         # attrs from importer class
#         # super().__init__(xml_file, config)
#
#         config = app.config
#         client = app.client
#
#         self.home_sender = client.sender(
#             address_id=config.home_sender_id,
#             name=config.home_address['contact'],
#             email=config.home_address['email'],
#             telephone=config.home_address['telephone'],
#             sender_address=client.get_sender_addresses()[0]
#         )
#         self.home_recipient = client.recipient(
#             name=config.home_address['contact'],
#             email=config.home_address['email'],
#             telephone=config.home_address['telephone'],
#             recipient_address=client.find_address(config.home_address['postal_code'],
#                                                   config.home_address['search_term'])
#
#         )
#
#         if DEBUG:
#             pprint(f"\n{self=}\n")


class Shipment():
    def __init__(self, app, ship_dict, is_return=False):
        """
        :param ship_dict: a dictionary of shipment details
        :param config: a config() object
        :param reference:
        :param label_text:
        """
        self.category = ship_dict['category']
        self.app = app
        self.shipment_name = ship_dict['shipment_name']
        self.date = ship_dict['send_out_date']
        self.address_as_str = ship_dict['address_as_str']
        self.contact = ship_dict['contact']
        self.company_name = None
        self.postcode = ship_dict['postcode']
        self.boxes = ship_dict['boxes']
        self.status = ship_dict['status']
        self.email = ship_dict['email']
        self.telephone = ship_dict['telephone']
        self.customer = ship_dict['customer']
        self.is_return = is_return
        self.inbound_id = ship_dict.get('inbound_id', None)
        self.outbound_id = ship_dict.get('outbound_id', None)
        self.service = None
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = False




        if DEBUG:
            print_and_long_pop(f"\n{self=}\n")

    def get_home_sender_recip(self):
        config = self.app.config
        client = self.app.client
        try:
            if self.is_return:
                self.recipient = client.get_sender_addresses()[0]
            else:
                self.sender = client.get_sender_addresses()[0]

        except Exception as e:
            print_and_pop(e.__repr__())


