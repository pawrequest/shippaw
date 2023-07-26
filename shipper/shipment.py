import logging
import re
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dbfread.dbf import DBF, DBFNotFound

from core.config import Config
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service, \
    ShipmentRequest, ShipmentReturn, Collection
from core.enums import BestMatch, Contact, DespatchObjects, ShipmentCategory
from core.exceptions import ShipDictError
from core.config import logger


@dataclass
class Shipment:
    def __init__(self, ship_dict: dict, category:ShipmentCategory):
        """
        :param ship_dict: a dictionary of shipment details
        """

        # input paramaters
        self.category= category.title()
        self._shipment_name: str = ship_dict.get('shipment_name')
        self._address_as_str: str = ship_dict.get('address_as_str')
        self.boxes: int = int(ship_dict.get('boxes', 1))
        self.customer: str = ship_dict.get('customer')
        self.contact_name: str = ship_dict.get('contact')
        self.email: str = ship_dict.get('email')
        self.postcode: str = ship_dict.get('postcode')
        self.send_out_date: datetime.date = ship_dict.get('send_out_date', datetime.today())
        self.status: str = ship_dict.get('status')
        self.telephone: str = ship_dict.get('telephone')
        self.delivery_name = ship_dict.get('delivery_name')
        self.inbound_id: Optional[str] = ship_dict.get('inbound_id')
        self.outbound_id: Optional[str] = ship_dict.get('outbound_id')

        self.printed = False
        self.date_menu_map = dict()
        self.service_menu_map: dict = dict()
        self.candidate_keys = {}
        self.parcels: [Parcel] = []
        self.label_location: Path = Path()

        self.remote_address: Address | None = None
        self.remote_contact: Optional[Contact] = None
        self.remote_sender_recip: Optional[Sender | Recipient] = None
        self.sender = Sender
        self.recipient = Recipient


        self.date_matched = False

        self.despatch_objects = DespatchObjects()

        self.collection_date: Optional[CollectionDate] = None

        self.shipment_request: Optional[ShipmentRequest] = None
        self.shipment_return: Optional[ShipmentReturn] = None
        self.service: Optional[Service] = None
        self.available_services: Optional[List[Service]] = None
        self.available_date: Optional[List[CollectionDate]] = None

        self.default_service_matched: bool = False
        self.bestmatch: Optional[BestMatch] = None
        self.logged_to_commence: bool = False
        self.remote_contact: Optional[Contact] = None

        [logging.info(f'SHIPMENT - {self._shipment_name.upper()} - {var} : {getattr(self, var)}') for var in vars(self)]
        logging.info('\n')

    def __eq__(self, other):
        return self._shipment_name == other._shipment_name


    @property
    def shipment_name_printable(self):
        return re.sub(r'[:/\\|?*<">]', "_", self._shipment_name)


    @property
    def customer_printable(self):
        return self.customer.replace("&", '"&"').replace("'", "''")

    def to_dict(self):
        allowed_types = [dict, str, tuple, list, int, float, set, bool, datetime, None]
        result = {}
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if type(attr_value) in allowed_types:
                result[attr_name] = attr_value
        return result


    @property
    def str_to_match(self):
        return parse_amherst_address_string(self._address_as_str)


    @classmethod
    def get_shipments(cls, config: Config, category: ShipmentCategory, dbase_file: str) -> list:
        logger.info(f'DBase file og = {dbase_file}')
        shipments: [Shipment] = []
        try:
            for record in DBF(dbase_file, encoding='cp1252'):
                [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
                try:
                    ship_dict = shipdict_from_dbase(record=record, import_mapping=config.import_mapping)
                    shipment = cls(ship_dict=ship_dict, category=category)
                    shipments.append(shipment)
                except Exception as e:
                    logger.exception(f'{record.__repr__()} - {e}')
                    continue

        except UnicodeDecodeError as e:
            logging.exception(f'DBASE import error with {dbase_file} \n {e}')
        except DBFNotFound as e:
            logger.exception(f'.Dbf or Dbt are missing \n{e}')
        except Exception as e:
            logger.exception(e)
            raise e
        return shipments


    @classmethod
    def from_dbase_record(cls, record, ship_dict, category):
        [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
        return cls(ship_dict=ship_dict, category=category)



class DbayShipment(Shipment):
    def __init__(self, ship_dict, category):
        super().__init__(category=category, ship_dict=ship_dict)

        self.parcels: [Parcel] = []
        self.remote_address: Address | None = None
        self.sender_contact = None
        self.remote_contact: Optional[Contact] = None
        self.remote_sender_recip: Optional[Sender | Recipient] = None
        self.sender = Sender
        # self.recipient_contact = None

        self.despatch_objects = DespatchObjects()
        self.recipient: Recipient
        self.collection_date: CollectionDate
        self.shipment_request: ShipmentRequest
        self.shipment_return: ShipmentReturn
        self.service: Service
        self.available_services: [List[Service]]
        self.collection: Collection

    @classmethod
    def get_dbay_shipments(cls, import_mapping: dict, category: ShipmentCategory, dbase_file: str):
        logger.info(f'DBase file = {dbase_file}')
        shipments_dict = {}
        shipments_list:[DbayShipment] = []
        try:
            for record in DBF(dbase_file):
                [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
                try:
                    ship_dict = shipdict_from_dbase(record=record, import_mapping=import_mapping)
                    shipment = DbayShipment.from_dbase_record(record=record, ship_dict=ship_dict, category=category)
                    shipments_dict.update({shipment.shipment_name_printable: shipment})
                    shipments_list.append(shipment)
                except Exception as e:
                    logger.exception(f'{record.__repr__()} - {e}')
                    continue

        except UnicodeDecodeError as e:
            logging.exception(f'DBASE import error with {dbase_file} \n {e}')
            raise e
        except DBFNotFound as e:
            logger.exception(f'.Dbf or Dbt are missing \n{e}')
            raise e
        except Exception as e:
            logger.exception(e)
            raise e
        # return shipments_dict
        return shipments_list



def get_dbay_shipments(import_mapping:dict, category: ShipmentCategory, dbase_file: str):
    logger.info(f'DBase file NEW = {dbase_file}')
    shipments_dict = {}
    try:
        for record in DBF(dbase_file):
            [logger.debug(f'DBASE RECORD - {k} : {v}') for k, v in record.items()]
            try:
                ship_dict = shipdict_from_dbase(record=record, import_mapping=import_mapping)
                shipment = DbayShipment.from_dbase_record(record=record, ship_dict=ship_dict, category=category)
                shipments_dict.update({shipment.shipment_name_printable: shipment})
            except Exception as e:
                logger.exception(f'{record.__repr__()} - {e}')
                continue

    except UnicodeDecodeError as e:
        logging.exception(f'DBASE import error with {dbase_file} \n {e}')
    except DBFNotFound as e:
        logger.exception(f'.Dbf or Dbt are missing \n{e}')
    except Exception as e:
        logger.exception(e)
        raise e
    return shipments_dict

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


def shipdict_from_dbase(record, import_mapping:dict):
    ship_dict_from_dbf = {}
    for k, v in record.items():
        if v:
            try:
                if isinstance(v, str):
                    v = v.split('\x00')[0]
                # v = re.sub(r'[:/\\|?*<">]', "_", v)
                # v = re.sub(r'[:/\\|?*<">]', "_", v)
                k = import_mapping.get(k, k)

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
