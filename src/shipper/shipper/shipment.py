import logging
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import PySimpleGUI as sg
from commence_py.commence import CmcContext
from dbfread import DBF, DBFNotFound
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service, \
    ShipmentRequest, ShipmentReturn
from pydantic import BaseModel, ConfigDict, model_validator

from .addresser import parse_address_string
from ..core.entities import AddressMatch, BestMatch, Contact, DateTimeMasks, ImportMap
from ..core.funcs import collection_date_to_datetime

logger = logging.getLogger(__name__)

FIELD_VARIATIONS = {
    'Delivery Telephone': 'Delivery Tel',
}


class ShipmentInput(BaseModel):
    """ input validated"""
    model_config = ConfigDict(extra='allow')
    is_dropoff: bool = False
    is_outbound: bool
    customer: str
    address_as_str: str
    boxes: int = 1
    contact_name: str
    email: str
    postcode: str
    send_out_date: date = datetime.today().date()
    telephone: str
    delivery_name: str
    inbound_id: Optional[str] = None
    outbound_id: Optional[str] = None
    shipment_name: Optional[str] = None
    remote_address_matched: AddressMatch = AddressMatch.NOT

    @classmethod
    def from_cmc_transaction(cls, table: str, transaction: str, outbound: bool = True):

        with CmcContext() as cmc:
            transaction = cmc.get_record_with_customer(table, transaction)

            in_data = {}
            for pyname, cmcname in shipment_fieldmap.items():
                if val := transaction.get(cmcname):
                    in_data[pyname] = val
                else:
                    try:
                        new_key = FIELD_VARIATIONS[cmcname]
                        in_data[pyname] = transaction[new_key]
                    except KeyError:
                        raise ValueError(f'No value for {cmcname} or {new_key} in {transaction}')

            return cls(
                model_config=ConfigDict(extra='allow'),
                is_dropoff=False,
                is_outbound=outbound,
                category=table,
                remote_address_matched=AddressMatch.NOT,
                **in_data
            )

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
        return parse_address_string(self.address_as_str)

    @property
    def customer_printable(self):
        return self.customer.replace("&", 'and')

    def __str__(self):
        return self.shipment_name_printable

    def __repr__(self):
        return self.shipment_name_printable

    def __eq__(self, other):
        return self.shipment_name == other.shipment_name


customer_fieldmap = dict(
    address_as_str='Deliv Address',
    contact_name='Deliv Contact',
    email='Deliv Email',
    delivery_name='Deliv Name',
    postcode='Deliv Postcode',
    telephone='Deliv Telephone',
)

shipment_fieldmap = dict(
    shipment_name='Name',
    address_as_str='Delivery Address',
    contact_name='Delivery Contact',
    email='Delivery Email',
    delivery_name='Delivery Name',
    postcode='Delivery Postcode',
    telephone='Delivery Telephone',
    customer='To Customer',
    boxes='Boxes',
    send_out_date='Send Out Date',
    send_method='Send Method',
    outbound_id='Outbound ID',
    inbound_id='Inbound ID',
)


class ShipmentAddressed(ShipmentInput):
    """address prep done"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    remote_contact: Contact
    remote_address: Address
    sender: Sender
    recipient: Recipient


class ShipmentAddressedNew(ShipmentInput):
    """address prep done"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    remote_contact: Contact
    remote_address: Address
    sender: Sender
    recipient: Recipient


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
    timestamp: str


class ShipmentCmcUpdated(ShipmentQueued):
    is_logged_to_commence: bool = False


class ShipmentBooked(ShipmentQueued):
    """ booked"""
    is_booked: bool = False
    shipment_return: ShipmentReturn


class ShipmentCompleted(ShipmentBooked):
    label_location: Path
    is_printed: bool = False
    is_emailed: bool = False


class ShipmentDict(dict[str, ShipmentRequested]):
    pass


def shipments_from_records(category, import_map: ImportMap, outbound: bool, records: [dict]) \
        -> List[ShipmentInput]:
    return [shipment_from_record(category=category, import_map=import_map, outbound=outbound,
                                 record=record) for record in records]


def shipment_from_record(category, import_map: ImportMap, outbound: bool, record: dict) \
        -> ShipmentInput | None:
    transformed_record = {k: record.get(v) for k, v in import_map.model_dump().items() if record.get(v)}
    transformed_record['delivery_name'] = transformed_record['contact_name'] or transformed_record[
        'delivery_name']
    [logger.info(f'TRANSFORMED RECORD - {k} : {v}') for k, v in transformed_record.items()]
    try:
        return ShipmentInput(**transformed_record, category=category, is_outbound=outbound)
    except Exception as e:
        logger.exception(f'SHIPMENT CREATION FAILED: {record.__repr__()} - {e}')
        return None


def contact_from_shipment(shipment: ShipmentInput):
    return Contact(name=shipment.contact_name, email=shipment.email, telephone=shipment.telephone)