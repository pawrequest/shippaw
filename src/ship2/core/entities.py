from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional, NamedTuple

from despatchbay.despatchbay_entities import Address
from pydantic import BaseModel


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


@dataclass
class DefaultCarrier:
    courier: int
    service: int

class DateTimeMasks(Enum):
    DISPLAY = '%A - %B %#d'
    HIRE = '%d/%m/%Y'
    DB = '%Y-%m-%d'
    BUTTON = '%A \n%B %#d'
    FILE = '%Y-%m-%d_%H-%M-%S'
    COMMENCE = '%Y%m%d'


class ApiScope(Enum):
    SAND = 'sandbox'
    PRODUCTION = 'production'


class FieldsList(Enum):
    contact = ['telephone', 'name', 'email']
    address = ['company_name', 'street', 'locality', 'town_city', 'county', 'postal_code']
    export = ['category', 'customer', 'boxes', 'recipient', 'sender', 'inbound_id',
              'outbound_id', 'shipment_name', 'timestamp']
    shipment = ['boxes', 'category', 'address_as_str', 'cost', 'email', 'postcode', 'telephone', 'search_term',
                'date', 'inbound_id', 'outbound_id', 'shipment_name']


@dataclass
class PathsList:
    def __init__(self):
        self.log_json: Path = Path()
        self.cmc_logger: Path = Path()
        self.cmc_installer: Path = Path()
        self.cmc_updater: Path = Path()
        self.cmc_dll: Path = Path()
        self.outbound_labels: Path = Path()
        self.inbound_labels: Path = Path()
        self.user_data = Path()
        self.dbase_export = Path()
        self.logfile = Path()

    @classmethod
    def from_dict(cls, paths_dict: dict, root_dir):
        pl = cls()
        for name, path in paths_dict.items():
            setattr(pl, name, root_dir / path)
        pl.outbound_labels.mkdir(parents=True, exist_ok=True)
        return pl


BestMatch = namedtuple('BestMatch', ['str_matched', 'address', 'category', 'score'])


@dataclass
class Contact:
    email: str
    telephone: str
    name: str


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


class ImportMap(BaseModel):
    address_as_str: str
    contact_name: str
    email: str
    delivery_name: str
    postcode: str
    telephone: str
    customer: str


class HireMap(ImportMap):
    shipment_name: str
    boxes: str
    send_out_date: str
    send_method: str
    outbound_id: str
    inbound_id: str


class SaleMap(ImportMap):
    shipment_name: str
    outbound_id: str
    inbound_id: str



class AddressMatch(Enum):
    DIRECT = auto()
    FUZZY = auto()
    NOT = auto()
    EXPLICIT = auto()
    GUI = auto()
