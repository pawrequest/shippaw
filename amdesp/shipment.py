import re

from amdesp.utils_pss.utils_pss import Utility, unsanitise
import xml.etree.ElementTree as ET
import PySimpleGUI as sg
from pathlib import Path
from dbfread import DBF
from amdesp.config import Config
from amdesp.despatchbay.despatchbay_entities import Service, Sender, Recipient, Parcel, ShipmentRequest

from datetime import datetime
import pathlib

from amdesp.despatchbay.despatchbay_entities import Service, Sender, Recipient, Parcel


class Shipment:
    def __init__(self, ship_dict: dict, is_return: bool = False):
        """
        :param ship_dict: a dictionary of shipment details
        :param is_return: recipient is user's own sender_address[0]
        """
        self.address_as_str: str = ship_dict['address_as_str']
        self.boxes: int = ship_dict['boxes']
        self.candidate_keys: list | None = None
        self.category: str = ship_dict['category']
        self.collection_booked: bool = False
        self.company_name: str = ''
        self.customer: str = ship_dict['customer']
        self.contact = next((ship_dict.get(key) for key in ['contact', 'contact_name'] if key in ship_dict), None)
        self.date_menu_map: dict = dict()
        self.date: datetime.date = ship_dict['date']
        self.email: str = ship_dict['email']
        self.inbound_id: str | None = ship_dict.get('inbound_id', None)
        self.is_return: bool = is_return
        self.label_location: pathlib.Path = pathlib.Path()
        self.outbound_id: str | None = ship_dict.get('outbound_id', None)
        self.parcels: [Parcel] = []
        self.postcode: str = ship_dict['postcode']
        self.printed: bool = False
        self.recipient: Recipient | None = None
        self.search_term: str | None = ship_dict.get('search_term', None)
        self.sender: Sender | None = None
        self.service: Service | None = None
        self.service_menu_map: dict = dict()
        self.shipment_name: str = ship_dict['shipment_name']
        self.shipment_request: ShipmentRequest|None = None
        self.status: str = ship_dict['status']
        self.telephone: str = ship_dict['telephone']

    @classmethod
    def get_shipments(cls, config: Config, in_file: str) -> list:
        """ parses input filetype and calls appropriate function to construct and return a list of shipment objects"""
        shipments = []
        file_ext = in_file.split('.')[-1]
        if file_ext == 'xml':
            ship_dict = ship_dict_from_xml(config=config, xml_file=in_file)
            try:
                shipments.append(Shipment(ship_dict=ship_dict))
            except KeyError as e:
                print(f"Shipdict Key missing: {e}")
        elif file_ext == 'dbf':
            shipments = cls.bulk_shipments_from_dbase(dbase_file=in_file)
            # shipments.append(cls.shipments_from_dbase(dbase_file=in_file))
        else:
            sg.popup("Invalid input file")
        return shipments

    @classmethod
    def bulk_shipments_from_dbase(cls, dbase_file):
        shipments = []
        for record in DBF(dbase_file):
            shipdict = cls.shipdict_from_dbase(record=record)
            shipment = Shipment(ship_dict=shipdict)
            shipments.append(shipment)
        return shipments

    @classmethod
    def shipdict_from_dbase(cls, record):
        # todo check thse
        # shipdict = {}
        # shipdict.update({'address_as_str': record.get('DELIVERY_A', '').split('\x00')[0]})
        # shipdict.update({'boxes': record.get('BOXES', 1)})
        # shipdict.update({'date': record.get('SEND_OUT_D', '') or datetime.today()})
        # shipdict.update({'category': 'Hire'})
        # shipdict.update({'contact': record.get('DELIVERY_C', '').split('\x00')[0]})
        # shipdict.update({'customer': record.get('FIELD17', '').split('\x00')[0]})
        # shipdict.update({'delivery_name': record.get('DELIVERY_N', '').split('\x00')[0]})
        # shipdict.update({'email': record.get('DELIVERY_E', '').split('\x00')[0]})
        # if inbound := record.get('INBOUND_ID'):
        #     shipdict.update({'inbound_ID': inbound.split('\x00')[0]})
        # if outbound := record.get('OUTBOUND_I'):
        #     shipdict.update({'inbound_ID': outbound.split('\x00')[0]})
        #
        # shipdict.update({'postcode': record.get('DELIVERY_P', '').split('\x00')[0]})
        # shipdict.update({'shipment_name': record.get('NAME', '').split('\x00')[0]})
        # shipdict.update({'status': record.get('STATUS', None)})
        # shipdict.update({'telephone': record.get('DELIVERY_T', '').split('\x00')[0]})

        ship_dict_from_dbf = {}
        for k, v in record.items():
            if isinstance(v, str):
                v = v.split('\x00')[0]
            match k:
                case 'DELIVERY_A':
                    k = 'address_as_str'
                case 'DELIVERY_C':
                    k = 'contact'
                case 'DELIVERY_E':
                    k = 'email'
                case 'DELIVERY_N':
                    k = 'delivery_name'
                case 'DELIVERY_P':
                    k = 'postcode'
                case 'DELIVERY_R':
                    k = 'delivery_ref'
                case 'DELIVERY_T':
                    k= 'telephone'
                case 'BOXES':
                    k='boxes'
                case 'DB_LABEL_P':
                    k='label_printed'
                case 'SEND___COL':
                    k = 'send_collect'
                case 'SEND_METHO':
                    k = 'send_method'
                case 'INBOUND_ID':
                    k = 'inbound_id'
                case 'OUTBOUND_I':
                    k = 'outbound_id'
                case 'STATUS':
                    k = 'status'
                case 'FIELD17':
                    k = 'customer'
                case 'NAME':
                    k = 'shipment_name'
                    v = re.sub(r"\W", "_", v)
                    ...
                case 'SEND_OUT_D':
                    k = 'date'

                case _:
                    sg.popup_error(f'{k}, {v}')
            ship_dict_from_dbf.update({k: v})



        ship_dict_from_dbf.update({'category':'Hire'})
        return ship_dict_from_dbf


def ship_dict_from_xml(config: Config, xml_file: str) -> dict:
    """parse amherst shipment xml"""
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

            if "number" in k.lower():
                # if not v.isnumeric():
                #     v = re.sub(r"\D", "", v)
                if 'serial' in k.lower():
                    v = [int(x) for x in v.split() if x.isdigit()]
                else:
                    if isinstance(v, str):
                        v = re.sub(r"\D", "", v)

                        # v = int(v.replace(',', ''))
            if k == 'name':
                k = 'shipment_name'
                v = "".join(ch if ch.isalnum() else '_' for ch in v)
            if k[:6] == "deliv ":
                k = k.replace('deliv', 'delivery')
            k = k.replace('delivery_', '')
            if k == 'tel':
                k = 'telephone'
            if k == 'address':
                k = 'address_as_str'
            ship_dict.update({k: v})

    # get customer name
    if category in ["Hire", "Sale"]:
        ship_dict['customer'] = root[0][3].text
    elif category == "Customer":
        ship_dict['customer'] = fields[0][1].text
        ship_dict[
            'shipment_name'] = f'{ship_dict["shipment_name"]} - {datetime.now().isoformat(" ", timespec="seconds")}'
    try:
        ship_dict['date'] = datetime.strptime(ship_dict['send_out_date'], config.datetime_masks['DT_HIRE'])
    except:
        ship_dict['date'] = datetime.today()
    ship_dict['category'] = category
    ship_dict['search_term'] = parse_amherst_address_string(ship_dict['address_as_str'])
    ship_dict['boxes'] = ship_dict.get('boxes', 1)

    missing = []
    for attr_name in shipment_fields:
        if attr_name not in ship_dict.keys():
            if attr_name not in ['cost', 'inbound_id', 'outbound_id']:
                missing.append(attr_name)
    if missing:
        sg.popup(f"*** Warning - {missing} not found in ship_dict - Warning ***")
    return ship_dict


def to_snake_case(input_string: str) -> str:
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string


def parse_amherst_address_string(str_address: str):
    first_block = str_address.split(" ")[0].split(",")[0]
    first_char = [first_block][0]
    firstline = re.sub(r'[^\w\s]+', '', str_address.split("\n")[0].strip())

    if first_char.isnumeric():
        return first_block
    else:
        return firstline
