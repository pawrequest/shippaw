import os
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

from despatchbay.despatchbay_entities import Address, CollectionDate, Service, ShipmentRequest, ShipmentReturn
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException


class ShipmentCategory(Enum):
    HIRE = 'HIRE'
    SALE = 'SALE'
    CUSTOMER = 'CUSTOMER'


@dataclass
class DateMenuMap:
    ...


@dataclass
class CandidateKeys:
    ...


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


class ShipMode(Enum):
    SHIP = 'SHIP'
    TRACK = 'TRACK'


class ShipDirection(Enum):
    IN = 'IN'
    OUT = 'OUT'



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
    filename = '%Y-%m-%d_%H-%M-%S'


class ApiScope(Enum):
    SAND = 'sandbox'
    PRODUCTION = 'production'


class FieldsList(Enum):
    contact = ['telephone', 'name', 'email']
    address = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']
    export = ['category', 'customer', 'boxes', 'recipient', 'sender', 'inbound_id',
              'outbound_id', '_shipment_name', 'timestamp']
    shipment = ['boxes', 'category', 'address_as_str', 'cost', 'email', 'postcode', 'telephone', 'search_term',
                'date', 'inbound_id', 'outbound_id', 'shipment_name']


@dataclass
class PathsList:
    def __init__(self):
        self.log_json: Path = Path()
        self.cmc_logger: Path = Path()
        self.cmc_installer: Path = Path()
        self.cmc_updater:Path = Path()
        self.cmc_updater_add:Path = Path()

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
