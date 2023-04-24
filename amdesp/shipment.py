import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dbfread.dbf import DBF, DBFNotFound

from amdesp.config import Config, get_amdesp_logger
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service, \
    ShipmentRequest, ShipmentReturn
from amdesp.enums import BestMatch, Contact, DespatchObjects
from amdesp.exceptions import *

logger = get_amdesp_logger()


@dataclass
class Shipment:
    def __init__(self, ship_dict: dict):
        """
        :param ship_dict: a dictionary of shipment details
        """

        self.address_as_str: str = ship_dict.get('address_as_str')
        self.str_to_match = ''.join(self.address_as_str.split('\r')[0:1]) \
            .replace('Units', 'Unit').replace('c/o ', '').replace('C/O ', '')
        self.boxes: int = int(ship_dict.get('boxes', 1))
        self.category: str = ship_dict.get('category')
        self.customer: str = ship_dict.get('customer')
        self.contact_name: str = ship_dict.get('contact')
        # self.contact_name: str = next((ship_dict.get(key) for key in ['contact', 'contact_name'] if key in ship_dict), None)
        self.email: str = ship_dict.get('email')
        self.postcode: str = ship_dict.get('postcode')
        self.send_out_date: datetime.date = ship_dict.get('send_out_date', datetime.today())
        self.shipment_name: str = ship_dict.get('shipment_name')
        self.status: str = ship_dict.get('status')
        self.telephone: str = ship_dict.get('telephone')
        self.shipment_name_printable = re.sub(r'[:/\\|?*<">]', "_", self.shipment_name)
        self.delivery_name = ship_dict.get('delivery_name')

        self.inbound_id: Optional[str] = ship_dict.get('inbound_id')
        self.outbound_id: Optional[str] = ship_dict.get('outbound_id')

        self.collection_booked = False
        self.printed = False
        self.date_menu_map = dict()
        self.service_menu_map: dict = dict()
        self.label_location: Path = Path()
        self.candidate_key_dict = {}
        self.parcels: [Parcel] = []

        self.remote_address: Address | None = None
        self.sender_contact = None
        self.sender = Sender
        # self.recipient_contact = None
        self.recipient = Recipient

        self.date_matched = False

        self.despatch_objects = DespatchObjects()

        self.collection_date: Optional[CollectionDate] = None


        self.shipment_request: Optional[ShipmentRequest] = None
        self.shipment_return: Optional[ShipmentReturn] = None
        self.service: Optional[Service] = None
        self.available_services:Optional[List[Service]] = None


        self.default_service_matched:bool = False
        self.bestmatch:Optional[BestMatch] = None
        self.logged_to_commence:bool = False


        [logging.info(f'SHIPMENT - {self.shipment_name.upper()} - {var} : {getattr(self, var)}') for var in vars(self)]

    def get_remote_contact(self):
        return Contact(email=self.email, telephone=self.telephone, name=self.contact_name)

    @classmethod
    def get_shipments(cls, config: Config) -> list:
        """ parses input filetype and calls appropriate function to construct and return a list of shipment objects"""
        shipments: [Shipment] = []
        dbase_file = str(config.paths.dbase_export)
        try:
            for record in DBF(dbase_file):
                [logger.info(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
                try:
                    ship_dict = shipdict_from_dbase(record=record, config=config)
                    shipment = Shipment(ship_dict=ship_dict)
                    shipments.append(shipment)
                except Exception as e:
                    raise ImportError(f'{record.__repr__()} - {e}')

        except UnicodeDecodeError as e:
            logging.exception(f'DBASE import error with {dbase_file} \n {e}')
        except DBFNotFound as e:
            logger.exception(f'.Dbf or Dbt are probably missing \n{e}')
        except Exception as e:
            logger.exception(e)

        return shipments

    def to_dict(self):
        allowed_types = [dict, str, tuple, list, int, float, set, bool, datetime, None]
        result = {}
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if type(attr_value) in allowed_types:
                result[attr_name] = attr_value
        return result

    def parse_amherst_address_string(self, str_address: str):
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


def shipdict_from_dbase(record, config: Config):
    # todo check thse

    mapping = config.import_mapping
    ship_dict_from_dbf = {'category': 'Hire'}
    for k, v in record.items():
        if v:
            try:
                if isinstance(v, str):
                    v = v.split('\x00')[0]
                # v = re.sub(r'[:/\\|?*<">]', "_", v)
                # v = re.sub(r'[:/\\|?*<">]', "_", v)
                k = mapping.get(k, k)

                logging.info(f'SHIPDICT FROM DBASE - {k} : {v}')
                ship_dict_from_dbf.update({k: v})
            except Exception as error:
                raise ShipDictError(f'ShipDictError: {k=},\n{v=}\n{error=}')

    return ship_dict_from_dbf


def to_snake_case(input_string: str) -> str:
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string
