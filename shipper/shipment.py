import os
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import PySimpleGUI as sg
from dbfread import DBF, DBFNotFound
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service, \
    ShipmentRequest, ShipmentReturn
from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator
from typing_extensions import Annotated

from core.config import ImportMap, logger
from core.enums import BestMatch, Contact, DateTimeMasks, ShipmentCategory
from core.funcs import collection_date_to_datetime


def parse_amherst_address_string(str_address: str):
    str_address = str_address.lower()
    words = str_address.split(" ")
    if 'unit' in ' '.join(words[:2]):
        first_block = ' '.join(words[:2])
    else:
        first_block = words[0].split(",")[0]
    first_char = first_block[0]
    firstline = str_address.split("\n")[0].strip()

    return first_block if first_char.isnumeric() else firstline


def commence_string(in_string: str):
    if '\x00' in in_string:
        in_string = in_string.split('\x00')[0]
    out_string = in_string.replace('\r\n', '\n')
    return out_string


MyStr = Annotated[str, BeforeValidator(commence_string)]


class ShipmentInput(BaseModel):
    """ input validated"""
    model_config = ConfigDict(extra='allow')
    is_dropoff: bool = False
    is_outbound: bool
    category: ShipmentCategory
    customer: MyStr
    address_as_str: MyStr
    boxes: int = 1
    contact_name: MyStr
    email: MyStr
    postcode: MyStr
    send_out_date: date = datetime.today().date()
    telephone: MyStr
    delivery_name: MyStr
    inbound_id: Optional[MyStr] = None
    outbound_id: Optional[MyStr] = None
    shipment_name: Optional[MyStr] = None

    @model_validator(mode='after')
    def ship_name(self) -> "ShipmentInput":
        if self.shipment_name is None:
            self.shipment_name = f'{self.customer} - {datetime.now():{DateTimeMasks.FILE.value}}'
        return self

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


class ShipmentPreRequest(ShipmentPrepared):
    collection_date: CollectionDate
    date_matched: bool
    service: Service
    default_service_matched: bool
    parcels: List[Parcel]

    @property
    def collection_date_datetime(self):
        return collection_date_to_datetime(self.collection_date)


class ShipmentRequested(ShipmentPreRequest):
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


def records_from_dbase(dbase_file: os.PathLike, encoding='iso-8859-1') -> List[Dict]:
    while not Path(dbase_file).exists():
        dbase_file = sg.popup_get_file('Select a .dbf file to import', file_types=(('DBF Files', '*.dbf'),))

    try:
        return [record for record in DBF(dbase_file, encoding=encoding)]
    except UnicodeDecodeError as e:
        logger.exception(f'Char decoding import error with {dbase_file} \n {e}')
    except DBFNotFound as e:
        logger.exception(f'.Dbf or Dbt are missing \n{e}')
    except Exception as e:
        logger.exception(e)

class ShipmentDict(dict[str, ShipmentInput]):
    pass
def shipments_from_records(category: ShipmentCategory, import_map: ImportMap, outbound: bool, records: [dict]) \
        -> List[ShipmentInput]:
    shipments = []
    for record in records:
        try:
            shipments.append(shipment_from_record(category=category, import_map=import_map, outbound=outbound,
                                                  record=record))
        except Exception as e:
            logger.exception(f'SHIPMENT CREATION FAILED: {record.__repr__()} - {e}')
            continue
    if not shipments:
        logger.info('No shipments to process.')
        sys.exit()
    return shipments

def shipments_from_records_dict(category: ShipmentCategory, import_map: ImportMap, outbound: bool, records: [dict]) \
        -> ShipmentDict:
    shipments = ShipmentDict()
    for record in records:
        try:
            shipment = shipment_from_record(category=category, import_map=import_map, outbound=outbound,
                                                  record=record)
            shipments[shipment.shipment_name] = shipment
        except Exception as e:
            logger.exception(f'SHIPMENT CREATION FAILED: {record.__repr__()} - {e}')
            continue
    if not shipments:
        logger.info('No shipments to process.')
        sys.exit()
    logger.info(f'{len(shipments)} shipments added to dict')

    return shipments


def shipment_from_record(category: ShipmentCategory, import_map: ImportMap, outbound: bool,
                         record: dict) -> ShipmentInput:
    transformed_record = {k: record.get(v) for k, v in import_map.model_dump().items() if record.get(v)}
    [logger.debug(f'TRANSFORMED RECORD - {k} : {v}') for k, v in transformed_record.items()]
    return ShipmentInput(**transformed_record, category=category, is_outbound=outbound)
