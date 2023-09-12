import logging
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

import PySimpleGUI as sg
from dbfread import DBF, DBFNotFound
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service, \
    ShipmentRequest, ShipmentReturn
from pydantic import BaseModel, ConfigDict, ValidationError

from core.config import logger
from core.enums import BestMatch, Contact, ShipmentCategory, DateTimeMasks
from core.funcs import get_type, collection_date_to_datetime


#
#
# def parse_amherst_address_string(str_address: str):
#     str_address = str_address.lower()
#     if 'unit' in ' '.join(str_address.split(" ")[0:2]):
#         first_block = ' '.join(str_address.split(" ")[0:2])
#         return first_block
#     else:
#         first_block = str_address.split(" ")[0].split(",")[0]
#     first_char = first_block[0]
#     # firstline = re.sub(r'[^\w\s]+', '', str_address.split("\n")[0].strip())
#     firstline = str_address.split("\n")[0].strip()
#
#     return first_block if first_char.isnumeric() else firstline


def parse_amherst_address_string(str_address: str):
    # Step 1: Convert the address string to lowercase
    str_address = str_address.lower()

    # Step 2: Split the address string into words
    words = str_address.split(" ")

    # Step 3: Check if the word 'unit' is in the first two words of the address
    if 'unit' in ' '.join(words[:2]):
        first_block = ' '.join(words[:2])
    else:
        # Step 4: If 'unit' is not in the first two words, set first_block to the part of the first word before any comma
        first_block = words[0].split(",")[0]

    # Step 5: Get the first character of the first_block
    first_char = first_block[0]

    # Step 6: Get the first line of the address string
    firstline = str_address.split("\n")[0].strip()

    # Step 7: Check if there is a "/" in the first block and notify the user if found
    # now in get valid shipment
    # if "/" in first_block:
    #     sg.popup_ok(
    #         "Beware: This address contains a '/', which might indicate a Scottish or unusual address format. "
    #         "Please check the address carefully.")

    # Step 8: Return first_block if the first character is numeric; otherwise, return firstline
    return first_block if first_char.isnumeric() else firstline


class ShipmentInput(BaseModel):
    """ input validated"""
    model_config = ConfigDict(extra='allow')
    is_dropoff: bool = False
    is_outbound: bool
    category: ShipmentCategory
    shipment_name: str
    address_as_str: str
    boxes: int
    customer: str
    contact_name: str
    email: str
    postcode: str
    send_out_date: date
    telephone: str
    delivery_name: str
    inbound_id: Optional[str] = ''
    outbound_id: Optional[str] = ''

    @property
    def shipment_name_printable(self):
        return re.sub(r'[:/\\|?*<">]', "_", self.shipment_name)

    @property
    def str_to_match(self):
        return parse_amherst_address_string(self.address_as_str)

    @property
    def customer_printable(self):
        return self.customer.replace("&", 'and')

    def __str__(self):
        return self.shipment_name_printable

    def __repr__(self):
        return self.shipment_name_printable

    def __eq__(self, other):
        return self.shipment_name == other.shipment_name


class ShipmentAddressed(ShipmentInput):
    """address prep done"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    remote_contact: Contact
    remote_address: Address
    sender: Sender
    recipient: Recipient
    # remote_sender_recip: Optional[Union[Sender, Recipient]]


class ShipmentPrepared(ShipmentAddressed):
    # todo bestmatch and cand keys should be in addressed?
    available_dates: List[CollectionDate]
    all_services: List[Service]
    date_menu_map: Dict
    service_menu_map: Dict
    bestmatch: Optional[BestMatch] = None
    candidate_keys: Optional[Dict] = None


class ShipmentForRequest(ShipmentPrepared):
    collection_date: CollectionDate
    date_matched: bool
    service: Service
    default_service_matched: bool
    parcels: List[Parcel]

    @property
    def collection_date_datetime(self):
        return collection_date_to_datetime(self.collection_date)


class ShipmentRequested(ShipmentForRequest):
    shipment_request: ShipmentRequest


class ShipmentGuiConfirmed(ShipmentRequested):
    is_to_book: bool
    is_to_print_email: bool


class ShipmentQueued(ShipmentGuiConfirmed):
    """ queued. ready to book"""
    shipment_id: str
    is_queued: bool


class ShipmentCmcUpdated(ShipmentQueued):
    is_logged_to_commence: bool = False


class ShipmentBooked(ShipmentQueued):
    """ booked"""
    is_booked: bool = False
    shipment_return: ShipmentReturn

    @property
    def collection_booked_string(self):
        return f"Collection Booked for {self.collection_date_datetime:{DateTimeMasks.DISPLAY.value}} -" if self.is_booked else ""
    @property
    def label_filename_outbound(self):
        return f'{self.customer_printable} - Shipping Label - {self.collection_booked_string} booked at {self.timestamp}'

    @property
    def label_filename_inbound(self):
        return f'{self.customer_printable} - Returns Label - {self.collection_booked_string} booked at {self.timestamp}'


class ShipmentCompleted(ShipmentBooked):
    label_location: Path
    is_printed: bool = False
    is_emailed: bool = False


def shipdict_from_record(outbound: bool, record: dict, category: ShipmentCategory, import_mapping: dict):
    ship_dict: dict = {}
    for k, v in record.items():
        if v:
            if isinstance(v, str):
                if '\x00' in v:
                    v = v.split('\x00')[0]
            k = import_mapping.get(k, k)

            logging.info(f'SHIPDICT FROM DBASE - {k} : {v}')
            ship_dict.update({k: v})

    ship_dict['shipment_name'] = ship_dict.get('shipment_name',
                                               f'{ship_dict["customer"]} - {datetime.now().isoformat(timespec="seconds")}')
    ship_dict['send_out_date'] = ship_dict.get('send_out_date', datetime.today().date())
    ship_dict['boxes'] = ship_dict.get('boxes', 1)

    ship_dict['category'] = category.value
    ship_dict['is_outbound'] = outbound
    return ship_dict


def to_snake_case(input_string: str) -> str:
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string


#
#
# @dataclass
# class Shipment:
#     def __init__(self, ship_dict: dict, category: ShipmentCategory):
#         """
#         :param ship_dict: a dictionary of shipment details
#         """
#
#         # input paramaters
#         self.is_dropoff: bool | None = None
#         self.is_outbound: bool | None = None
#         self.category = category.name.title()
#         self.shipment_name: str = ship_dict.get('shipment_name')
#         self.address_as_str: str = ship_dict.get('address_as_str')
#         self.boxes: int = int(ship_dict.get('boxes', 1))
#         self.customer: str = ship_dict.get('customer')
#         self.contact_name: str = ship_dict.get('contact')
#         self.email: str = ship_dict.get('email')
#         self.postcode: str = ship_dict.get('postcode')
#         self.send_out_date: datetime.date = ship_dict.get('send_out_date', datetime.today())
#         self.status: str = ship_dict.get('status')
#         self.telephone: str = ship_dict.get('telephone')
#         self.delivery_name = ship_dict.get('delivery_name')
#         self.inbound_id: Optional[str] = ship_dict.get('inbound_id')
#         self.outbound_id: Optional[str] = ship_dict.get('outbound_id')
#
#         self.printed = False
#         self.date_menu_map = dict()
#         self.service_menu_map: dict = dict()
#         self.candidate_keys = {}
#         self.parcels: [Parcel] = []
#         self.label_location: Path = Path()
#
#         self.remote_address: Address | None = None
#         self.remote_contact: Optional[Contact] = None
#         self.remote_sender_recip: Optional[Sender | Recipient] = None
#         self.sender = Sender
#         self.recipient = Recipient
#
#         self.date_matched = False
#
#         self.despatch_objects = DespatchObjects()
#
#         self.collection_date: Optional[CollectionDate] = None
#
#         self.shipment_request: Optional[ShipmentRequest] = None
#         self.shipment_return: Optional[ShipmentReturn] = None
#         self.service: Optional[Service] = None
#         self.available_services: Optional[List[Service]] = None
#         self.available_date: Optional[List[CollectionDate]] = None
#
#         self.default_service_matched: bool = False
#         self.bestmatch: Optional[BestMatch] = None
#         self.logged_to_commence: bool = False
#         self.remote_contact: Optional[Contact] = None
#
#         [logging.info(f'SHIPMENT - {self.shipment_name.upper()} - {var} : {getattr(self, var)}') for var in vars(self)]
#         logging.info('\n')
#
#     def __eq__(self, other):
#         return self.shipment_name == other.shipment_name
#
#     def str(self):
#         return self.shipment_name_printable
#
#     def __repr__(self):
#         return self.shipment_name_printable
#
#     @property
#     def shipment_name_printable(self):
#         return re.sub(r'[:/\\|?*<">]', "_", self.shipment_name)
#
#     @property
#     def customer_printable(self):
#         return self.customer.replace("&", '"&"').replace("'", "''")
#
#     @property
#     def str_to_match(self):
#         return parse_amherst_address_string(self.address_as_str)
#
#     @classmethod
#     def from_dbase_record(cls, record, ship_dict, category):
#         [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
#         return cls(ship_dict=ship_dict, category=category)


...


def get_valid_shipment(input_dict: dict) -> ShipmentInput:
    while True:
        try:
            shippy = ShipmentInput(**input_dict)
        except ValidationError as e:
            for error in e.errors():
                field = error['loc'][0]
                expected_type = get_type(cls=ShipmentInput, field=field)
                new_value = sg.popup_get_text(
                    f"Validation Error for {field}. Enter correct value (of type '{expected_type}')")
                input_dict[field] = new_value
        else:
            if "/" in shippy.address_as_str:
                sg.popup_ok(
                    "Beware: This address contains a '/', which might indicate a Scottish or unusual address format. "
                    "Please check the address carefully.")
            return shippy


def records_from_dbase(dbase_file: os.PathLike, encoding='iso-8859-1') -> List[Dict]:
    if not Path(dbase_file).exists():
        file = sg.popup_get_file('Select a .dbf file to import', file_types=(('DBF Files', '*.dbf'),))
        if not file:
            raise FileNotFoundError(f'{dbase_file} not found')

    try:
        return [record for record in DBF(dbase_file, encoding=encoding)]
    except UnicodeDecodeError as e:
        logger.exception(f'Char decoding import error with {dbase_file} \n {e}')
    except DBFNotFound as e:
        logger.exception(f'.Dbf or Dbt are missing \n{e}')
    except Exception as e:
        logger.exception(e)


def shipments_from_records(category: ShipmentCategory, import_map: dict, outbound: bool,
                           records: [dict]) -> List[ShipmentInput]:
    shipments = []
    for record in records:
        [logger.info(f'INPUT RECORD - {k} : {v}') for k, v in record.items()]
        try:
            ship_dict = shipdict_from_record(outbound=outbound, record=record,
                                             category=category, import_mapping=import_map)
            shipments.append(get_valid_shipment(input_dict=ship_dict))

        except Exception as e:
            logger.exception(f'SHIPMENT CREATION FAILED: {record.__repr__()} - {e}')
            continue

    return shipments
