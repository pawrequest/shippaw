import logging
from dataclasses import field
from datetime import datetime
from numbers import Number
from pathlib import Path
from typing import Dict, List, Optional, Union

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service, \
    ShipmentRequest, ShipmentReturn
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass

from core.config import logger
from core.enums import BestMatch, Contact, DespatchObjects, ShipmentCategory
from core.funcs import get_type


#

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


class ParcelValid(BaseModel, Parcel):
    ...

class ShipmentInput(BaseModel):
    is_dropoff: bool = False
    is_outbound: bool
    category: ShipmentCategory
    shipment_name: str
    address_as_str: str
    boxes: int
    customer: str
    contact: str
    email: str
    postcode: str
    send_out_date: datetime
    telephone: str
    delivery_name: str
    inbound_id: Optional[str] = ''
    outbound_id: Optional[str] = ''

class ShipmentAddressed(ShipmentInput):
    remote_address: Optional[Address]
    remote_contact: Optional[Contact]
    remote_sender_recip: Optional[Union[Sender, Recipient]]
class ShipmentToRequest(ShipmentAddressed):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    parcels: List[Parcel] = field(default_factory=list)
    sender: Sender = field(default_factory=Sender)
    recipient: Recipient = field(default_factory=Recipient)
    collection_date: CollectionDate
    available_dates: List[CollectionDate]
    available_services: List[Service]
    service: Service
    bestmatch: Optional[BestMatch] = None
    candidate_keys: Optional[Dict] = field(default_factory=dict)
    date_matched: bool = False
    date_menu_map: Dict = field(default_factory=dict)
    service_menu_map: Dict = field(default_factory=dict)
    default_service_matched: bool = False

class ShipmentRequested(ShipmentToRequest):
    shipment_request: Optional[ShipmentRequest] = None


class ShipmentConfirmed(ShipmentRequested):
    logged_to_commence: bool = False
    shipment_return: Optional[ShipmentReturn] = None
    service: Optional[Service] = None
    printed: bool = False
    label_location: Path = field(default_factory=Path)


def shipdict_from_record(outbound: bool, record: dict, category: ShipmentCategory, import_mapping: dict):
    ship_dict_from_dbf: dict = {}
    for k, v in record.items():
        if v:
            if isinstance(v, str):
                if '\x00' in v:
                    v = v.split('\x00')[0]
            k = import_mapping.get(k, k)

            logging.info(f'SHIPDICT FROM DBASE - {k} : {v}')
            ship_dict_from_dbf.update({k: v})

    ship_dict_from_dbf['shipment_name'] = ship_dict_from_dbf.get('shipment_name',
                                                                 f'{ship_dict_from_dbf["customer"]} - {datetime.now().isoformat(timespec="seconds")}')
    ship_dict_from_dbf['category'] = category.value
    ship_dict_from_dbf['is_outbound'] = outbound
    return ship_dict_from_dbf


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
            return shippy
