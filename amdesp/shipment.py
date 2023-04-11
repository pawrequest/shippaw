import re

from amdesp.utils_pss.utils_pss import Utility, unsanitise
import xml.etree.ElementTree as ET
import PySimpleGUI as sg
from pathlib import Path
from dbfread import DBF
from amdesp.config import Config
from amdesp.despatchbay.despatchbay_entities import Service, Sender, Recipient, Parcel, ShipmentRequest, CollectionDate, \
    Address, ShipmentReturn

from datetime import datetime
import pathlib

from amdesp.despatchbay.despatchbay_entities import Service, Sender, Recipient, Parcel


class Shipment:
    def __init__(self, ship_dict: dict, is_return: bool = False):
        """
        :param ship_dict: a dictionary of shipment details
        :param is_return: recipient is user's own sender_address[0]
        """
        self.address_as_str: str = ship_dict.get('address_as_str')
        self.str_to_match = ''.join(self.address_as_str.split('\r')[0:1]).replace('Units', 'Unit').replace('c/o ',
                                                                                                           '').replace(
            'C/O ', '')
        self.search_term: str = parse_amherst_address_string(str_address=self.str_to_match)
        self.boxes: int = int(ship_dict.get('boxes', 1))
        self.category: str = ship_dict.get('category')
        self.customer: str = ship_dict['customer']
        self.contact: str = next((ship_dict.get(key) for key in ['contact', 'contact_name'] if key in ship_dict), None)
        self.email: str = ship_dict.get('email')
        self.postcode: str = ship_dict.get('postcode')
        self.send_out_date: datetime.date = ship_dict.get('send_out_date', datetime.today().date())
        self.shipment_name: str = ship_dict.get('shipment_name')
        self.status: str = ship_dict.get('status')
        self.telephone: str = ship_dict.get('telephone')

        self.is_return: bool = is_return
        self.inbound_id: str | None = ship_dict.get('inbound_id')
        self.outbound_id: str | None = ship_dict.get('outbound_id')

        self.collection_booked = False
        self.printed = False
        self.company_name = str()
        self.date_menu_map = dict()
        self.service_menu_map: dict = dict()
        self.label_location: pathlib.Path = pathlib.Path()

        self.candidate_key_dict = {}
        self.parcels: [Parcel] = []
        self.remote_address: Address | None = None
        self.collection_date: CollectionDate | None = None
        self.recipient: Recipient | None = None
        self.sender: Sender | None = None
        self.shipment_request: ShipmentRequest | None = None
        self.shipment_return: ShipmentReturn | None = None
        self.service: Service | None = None
        self.available_services = None
        self.default_service_matched = False
        self.bestmatch = None
        self.logged_to_commence = None

    def get_sender_or_recip(self):
        return self.sender if self.is_return else self.recipient

    @classmethod
    def get_shipments(cls, config: Config, in_file: str) -> list:
        """ parses input filetype and calls appropriate function to construct and return a list of shipment objects"""
        shipments: [Shipment] = []
        file_ext = in_file.split('.')[-1].lower()
        try:
            if file_ext == 'xml':
                ship_dict = ship_dict_from_xml(config=config, xml_file=in_file)
                shipments.append(Shipment(ship_dict=ship_dict))


            elif file_ext == 'dbf':
                dbase_file = in_file
                for record in DBF(dbase_file):
                    shipdict = shipdict_from_dbase(record=record, config=config)
                    shipment = Shipment(ship_dict=shipdict)
                    shipments.append(shipment)

        except Exception as e:
            sg.popup(f"Error: {e}"
                     f"Input file = {in_file}"
                     f"Config: {config.__repr__()}"
                     f"Shipments: f'{(shipment.shipment_name for shipment in shipments if shipments)}'")
        else:
            return shipments


def shipdict_from_dbase(record, config: Config):
    # todo check thse

    mapping = config.import_mapping
    ship_dict_from_dbf = {}
    for k, v in record.items():
        if isinstance(v, str):
            v = v.split('\x00')[0]
        k = mapping[k]
        if k == 'shipment_name':
            v = re.sub(r"\W", "_", v)
        ship_dict_from_dbf.update({k: v})

    ship_dict_from_dbf.update({'category': 'Hire'})
    return ship_dict_from_dbf

    # @classmethod
    # def bulk_shipments_from_dbase(cls, dbase_file, config: Config):
    #     shipments = []
    #     for record in DBF(dbase_file):
    #         shipdict = cls.shipdict_from_dbase(record=record, config=config)
    #         shipment = Shipment(ship_dict=shipdict)
    #         shipments.append(shipment)
    #     return shipments


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
    str_address = str_address.lower()
    if 'unit' in ' '.join(str_address.split(" ")[0:2]):
        first_block = ' '.join(str_address.split(" ")[0:2])
        return first_block
    else:
        first_block = str_address.split(" ")[0].split(",")[0]
    first_char = first_block[0]
    # firstline = re.sub(r'[^\w\s]+', '', str_address.split("\n")[0].strip())
    firstline = str_address.split("\n")[0].strip()

    return first_block if first_char.isnumeric() else firstline


"""
def parse_amherst_address_string(str_address: str):
    first_block = str_address.split(" ")[0].split(",")[0]
    first_char = [first_block][0]
    firstline = re.sub(r'[^\w\s]+', '', str_address.split("\n")[0].strip())

    if first_char.isnumeric():
        return first_block
    else:
        return firstline

"""
