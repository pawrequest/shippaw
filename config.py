import os
import pathlib

from pyexcel_ods3 import get_data

from python.despatchbay.despatchbay_sdk import DespatchBaySDK

line = '-' * 100

####  PATHS ########
DIR_ROOT = pathlib.Path("/Amdesp")
DIR_DATA = pathlib.Path("/Amdesp/data/")
CONFIG_PATH = {
    'DIR_LABEL': DIR_DATA / "Parcelforce Labels",
    'JSONFILE': DIR_DATA / "AmShip.json",
    'XMLFILE': DIR_DATA.joinpath('AmShip.xml'),
    'LOGFILE': DIR_DATA.joinpath("AmLog.json"),
    'CONFIG_FILE': DIR_DATA.joinpath("AmDespConfig.Ods"),
}
pathlib.Path(DIR_DATA / "Parcelforce Labels").mkdir(parents=True, exist_ok=True)  # make the labels dirs (and parents)

CONFIG_FIELD = {
    'EXPORT_EXCLUDE_KEYS': ["addressObject", "dateObject", 'service_object', 'services', 'parcels', 'shipment_return'],
    'SHIPFIELDS': ["deliveryName", "deliveryContact", "deliveryTel", "deliveryEmail", "deliveryAddress",
                   "deliveryPostcode", "sendOutDate", "referenceNumber"],
    'HIREFIELDS': ['deliveryTel', 'boxes', 'deliveryCharge', 'deliveryContact', 'deliveryName', 'deliveryEmail',
                   'deliveryAddress', 'sendOutDate', 'sendOutDate', 'deliveryPostcode', 'referenceNumber',
                   'customer']}

## Despatch Bay
API_USER = os.getenv("DESPATCH_API_USER")
API_KEY = os.getenv("DESPATCH_API_KEY")
SENDER_ID = "5536"  # should be env var?
CLIENT = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
SENDER = CLIENT.sender(address_id=SENDER_ID)

## get class schema
CONFIG_CLASS = {}
CONFIG_RADIO = {}


def get_product_attrs():
    global CONFIG_CLASS
    # sheets = get_data(config)
    sheets = get_data(str(CONFIG_PATH['CONFIG_FILE']))
    # config_dict = dict()
    attrs = sheets['PRODUCT_ATTRS']
    for field in attrs:
        if field:
            k = field[0]
            v = field[1:]
            CONFIG_CLASS.update({k: v})
get_product_attrs()

def get_radios():
    global CONFIG_RADIO
    sheets = get_data(str(CONFIG_PATH['CONFIG_FILE']))
    # RADIO_DICT = dict()
    radios = sheets['RADIO_DICT']
    headers = radios[0]
    for radio in radios[1:]:
        if radio:
            k = radio[0] + radio[1]
            v = dict()
            for d, header in enumerate(headers):
                v.update({headers[d]: radio[d]})
            CONFIG_RADIO.update({k: v})


get_radios()
