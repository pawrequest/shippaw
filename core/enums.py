import os
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Any, List, Optional

from despatchbay.despatchbay_entities import Address, CollectionDate, Service, ShipmentRequest, ShipmentReturn
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException


class ShipmentCategory(StrEnum):
    HIRE = auto()
    SALE = auto()
    FAKE = auto()
    DROP = auto()


class GuiColIndex(Enum):
    CONTACT = 0
    SENDER = 1
    RECIPIENT = 2
    DATE = 3
    BOXES = 4
    SERVICE = 5
    ADD = 6
    BOOK = 7
    PRINT_EMAIL = 8


@dataclass
class DateMenuMap:
    ...


#
# @dataclass
# class BookingJob:
#     shipment_request: ShipmentRequest
#     book: bool
#     outbound: bool
#     print_or_email: bool
#     label_str:str
#     result: Optional[str] = None
#     timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
#
#     @classmethod
#     def from_shipment(cls, shipment:Shipment, book:bool, print_or_email:bool):
#         return cls(
#             shipment_request=shipment.shipment_request,
#             book=book,
#             print_or_email=print_or_email,
#             label_str=shipment.shipment_name_printable,
#             la
#
#         )


class FuzzyScoresEnum(Enum):
    customer_to_company = 'customer_to_company'
    str_to_company = 'str_to_company'
    str_to_street = 'str_to_street'


@dataclass
class FuzzyScores:
    address: Address
    str_matched: str
    customer_to_company: str
    str_to_company: str
    str_to_street: str

    @property
    def scores(self):
        return {
            FuzzyScoresEnum.customer_to_company: self.customer_to_company,
            FuzzyScoresEnum.str_to_company: self.str_to_company,
            FuzzyScoresEnum.str_to_street: self.str_to_street,
        }


class ShipMode(StrEnum):
    SHIP_OUT = auto()
    SHIP_IN = auto()
    TRACK = auto()
    FAKE = auto()
    DROP = auto()


@dataclass
class DbayCreds:
    api_user: str
    api_key: str

    @classmethod
    def from_dict(cls, api_name_user, api_name_key):
        return cls(api_user=os.environ.get(api_name_user),
                   api_key=os.environ.get(api_name_key))

    def validate(self):
        try:
            return DespatchBaySDK(api_user=self.api_user, api_key=self.api_key).get_account()
        except AuthorizationException as e:
            return None


@dataclass
class DefaultShippingService:
    courier: int
    service: int


class DateTimeMasks(Enum):
    DISPLAY = '%A - %B %#d'
    hire = '%d/%m/%Y'
    DB = '%Y-%m-%d'
    button_label = '%A \n%B %#d'


class ApiScope(Enum):
    SAND = 'sandbox'
    PRODUCTION = 'production'


class FieldsList(Enum):
    contact = ['telephone', 'name', 'email']
    address = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']
    export = ['category', 'collection_booked', 'customer', 'boxes', 'recipient', 'sender', 'inbound_id',
              'outbound_id', '_shipment_name', 'timestamp']
    shipment = ['boxes', 'category', 'address_as_str', 'cost', 'email', 'postcode', 'telephone', 'search_term',
                'date', 'inbound_id', 'outbound_id', 'shipment_name']


@dataclass
class PathsList:
    def __init__(self):
        self.log_json: Path = Path()
        self.cmc_logger: Path = Path()
        self.cmc_installer: Path = Path()
        self.cmc_dll: Path = Path()
        self.labels: Path = Path()
        self.user_data = Path()
        self.dbase_export = Path()

    @classmethod
    def from_dict(cls, paths_dict: dict, root_dir):
        pl = cls()
        for name, path in paths_dict.items():
            setattr(pl, name, root_dir / path)
        pl.labels.mkdir(parents=True, exist_ok=True)
        return pl


BestMatch = namedtuple('BestMatch', ['str_matched', 'address', 'category', 'score'])


# Contact = namedtuple('Contact', ['email', 'telephone', 'name'])
@dataclass
class Contact:
    email: str
    telephone: str
    name: str


class GuiMap(Enum):
    shipment_name = 'Shipment Name'
    boxes = 'Boxes'
    category = 'Category'
    delivery_address = 'Delivery Address'
    delivery_contact = 'Delivery Contact'
    delivery_email = 'Delivery Email'
    delivery_postcode = 'Delivery Postcode'
    delivery_tel = 'Delivery Tel'
    delivery_telephone = 'Delivery Telephone'
    search_term = 'Search Term'
    send_out_date = 'Send Out Date'
    inbound_id = 'Inbound ID'
    outbound_id = 'Outbound ID'
    county = 'County'
    town_city = 'Town / City'
    company_name = 'Company Name'
    postal_code = 'Postcode'


@dataclass
class DespatchObjects:
    # collection_date: Optional[CollectionDate] = None
    collection_date: Optional[CollectionDate] = None
    available_dates: Optional[List[CollectionDate]] = None
    shipment_request: Optional[ShipmentRequest] = None
    shipment_return: Optional[ShipmentReturn] = None
    service: Optional[Service] = None
    available_services: Optional[List[Service]] = None

    #
    # available_dates: Optional[List[CollectionDate]] = None
    # shipment_request: Optional[ShipmentRequest] = None
    # shipment_return: Optional[ShipmentReturn] = None
    # service: Optional[Service] = None
    # available_services: Optional[List[Service]] = None


@dataclass
class Email:
    from_address: str
    to_address: str
    body: str
    attachments: Any
    subject: str


@dataclass
class HomeAddress:
    address_id: int
    dbay_key: str
    company_name: str
    street: str
    locality: Optional[str]
    town_city: Optional[str]
    county: Optional[str]
    postal_code: str
    country_code: Optional[str] = 'GB'
    dropoff_sender_id: Optional[int] = None
