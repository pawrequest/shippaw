from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import PySimpleGUI as sg

from amdesp.despatchbay.despatchbay_entities import Address, ShipmentRequest


@dataclass
class Job:
    shipment_request: ShipmentRequest
    shipment_id: str
    add: bool
    book: bool
    print_or_email: bool


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
    ship_out, ship_in, track_in, track_out = range(1, 5)


@dataclass
class DbayCreds:
    scope: str  # get from enum
    api_user: str = None
    api_key: str = None


@dataclass
class DateTimeMasks:
    display = str()
    hire = str()
    db = str()
    button_label = str()

    @classmethod
    def from_dict(cls, mask_dict):
        masks = cls()
        for maskname, mask in mask_dict.items():
            setattr(masks, maskname, mask)
        return masks


@dataclass
class DefaultShippingService:
    courier = int()
    service = int()

    @classmethod
    def from_dict(cls, courier_dict):
        dss = cls()
        for key, name in courier_dict.items():
            setattr(dss, key, name)
        return dss


class ApiScope(Enum):
    SAND = 'sandbox'
    PRODUCTION = 'production'


@dataclass
class FieldsList:
    def __init__(self):
        self.address = [str()]
        self.contact = [str()]
        self.export = [str()]
        self.shipment = [str()]

    @classmethod
    def from_dict(cls, fields_list_dict):
        fields_list = cls()
        for field_type, field_list in fields_list_dict.items():
            if not field_list:
                field_list = sg.popup_get_text(
                    f'{field_type.title()} Field list not found, please enter a comma separated list')
                field_list = [field_list.split(',')]
                fields_list_dict[field_type] = field_list
            setattr(fields_list, field_type, field_list)
        return fields_list


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
Contact = namedtuple('Contact', ['email', 'telephone', 'name'])
