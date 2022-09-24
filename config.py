# PYTHON_EXE = ROOT_DIR / "python" / "bin" / "python.exe"
# PYTHON_MAIN_SCRIPT = ROOT_DIR / "main.py"
# COMMENCE_WRAPPER = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"

import os
import pathlib

from python.despatchbay.despatchbay_sdk import DespatchBaySDK

####  PATHS ########

ROOT_DIR = pathlib.Path("/Amdesp/")
DATA_DIR = ROOT_DIR / "data"
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
JSONFILE = DATA_DIR / "AmShip.json"
XMLFILE = DATA_DIR.joinpath('AmShip.xml')
XMLCUSTOMERSTR = "root[0][1].text"
LOGFILE = DATA_DIR.joinpath("AmLog.json")
pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)  # make the shipmentJson dirs

## Despatch Bay
API_USER = os.getenv("DESPATCH_API_USER")
API_KEY = os.getenv("DESPATCH_API_KEY")
SENDER_ID = "5536"  # should be env var?
CLIENT = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
SENDER = CLIENT.sender(address_id=SENDER_ID)

line = '-' * 100

## Field Control
EXPORT_EXCLUDE_KEYS = ["addressObject", "dateObject", 'service_object', 'services', 'parcels', 'shipment_return']
SHIPFIELDS = ["deliveryName", "deliveryContact", "deliveryTel", "deliveryEmail", "deliveryAddress",
                  "deliveryPostcode", "sendOutDate", "referenceNumber"]

HIREFIELDS = ['deliveryTel', 'boxes', 'deliveryCharge', 'deliveryContact', 'deliveryName', 'deliveryEmail',
              'deliveryAddress', 'sendOutDate', 'sendOutDate', 'deliveryPostcode', 'referenceNumber',
              'customer']


