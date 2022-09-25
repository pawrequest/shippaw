import os
import pathlib

from pyexcel_ods3 import get_data

from python.despatchbay.despatchbay_sdk import DespatchBaySDK

line = '-' * 100

# sheets = get_data(r"C:\AmDesp\data\AmDespConfig.ods")
# sheets = get_data(CONFIG_FILE)
# clarts_dict = dict()
# attrs = sheets['CLASS_ATTRS']
# for field in attrs:
#     if field:
#         k = field[0]
#         v = field[1:]
#         clarts_dict.update({k: v})


####  PATHS ########

ROOT_DIR = pathlib.Path("/Amdesp/")
DATA_DIR = ROOT_DIR / "data"
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
JSONFILE = DATA_DIR / "AmShip.json"
XMLFILE = DATA_DIR.joinpath('AmShip.xml')
XMLCUSTOMERSTR = "root[0][1].text"
LOGFILE = DATA_DIR.joinpath("AmLog.json")
CONFIG_FILE = DATA_DIR.joinpath("AmDespConfig.Ods")
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

CLASS_LIST = []
config=str(CONFIG_FILE)
sheets = get_data(config)
CLASS_CONFIG = dict()

for k in sheets.keys():
    CLASS_LIST.append(k)

# def get_config_ods(config=CONFIG_FILE):
for clart in CLASS_LIST:
    attrs = sheets[clart]
    for field in attrs:
        if field:
            k = field[0]
            v = field[1:]
            CLASS_CONFIG.update({k: v})
print(clart)
    # get_config_ods()

