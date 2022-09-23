import os
import pathlib

from python.despatchbay.despatchbay_sdk import DespatchBaySDK

####  CONFIG PATHS HERE ########
ROOT_DIR = pathlib.Path("/")
AMDESP_DIR = ROOT_DIR / "AmDesp"

# ROOT_DIR = os.path.abspath(ROOT_DIR)
sender_id = "5536"  # should be env var?
API_USER = os.getenv("DESPATCH_API_USER")
API_KEY = os.getenv("DESPATCH_API_KEY")
DATA_DIR = AMDESP_DIR / "data"
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
# LABEL_DIR = RootDirAbs + "Parcelforce Labels"
# PYTHON_EXE = ROOT_DIR / "python" / "bin" / "python.exe"
# PYTHON_MAIN_SCRIPT = ROOT_DIR / "main.py"
# COMMENCE_WRAPPER = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
JSONFILE = DATA_DIR / "AmShip.json"
# JSONFILE = RootDirAbs + "AmShip.json"
XMLFILE = DATA_DIR / "AmShip.xml"
XMLCUSTOMERSTR = "root[0][1].text"

LOGFILE = (DATA_DIR / "AmLog.json")

client = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
sender = client.sender(address_id=sender_id)
pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)  # make the shipmentJson dirs

################
### removing becasue in class
# client = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
# sender = client.sender(address_id=sender_id)
# courier_id = 8  # parcelforce


# with open(JSONFILE) as j:
#     pass
line = '-' * 100
# com_cols_lower = {'delivery tel': 'phone', 'delivery email': 'email', 'delivery address': 'address',
#             'send out date': 'send date', 'delivery postcode': 'postcode', 'reference number': 'hire ref',
#             "deliv name": "deliveryCustomer", "deliv address": "address", "deliv deliveryContact": "deliveryContact", "deliv email": "email",
#             "deliv postcode": "postcode", "deliv telephone": "tel"}

# new_com = {key.title(): value for (key, value) in com_cols.items()}

com_fields = {} # 'Reference Number': 'hire ref', 'Deliv Name': 'customer', 'Deliv Address': 'Delivery address',
              # 'Deliv Contact': 'delivery contact', 'Deliv Email': 'delivery email',
              # 'Delivery Postcode': 'delivery postcode',
              # 'Deliv Telephone': 'delivery tel'

export_exclude_keys = ["addressObject", "dateObject", 'service_object', 'services', 'parcels', 'shipment_return']
field_fixes = {}
expungedFields = []  # "Name" "toCustomer",
addFields = {}
shipmentFields = ["deliveryName", "deliveryContact", "deliveryPhone", "deliveryEmail", "deliveryAddress", "deliveryPostcode"]

hireFields = ['deliveryTel', 'boxes', 'deliveryCharge', 'deliveryName','deliveryEmail', 'deliveryAddress', 'sendOutDate', 'deliveryPostcode', 'referenceNumber', 'To Customer"']

# #  other fields
# is_shipped = "is collection booked"
# added_shipment = "despatch added shipment"
# building_num = "building num"
# address_firstline = "address first line"
# searchterm = "search term"
# shipnum = "shipment number"
# shipping_service_id = "shipment service id"
# shippingServiceName = "shipping service name"
# shippingCost = "shipping cost"
# desp_shipment_id = "despatch id"
# candidates = "candidates"
# date_check = "date check"
# category = "category"  # hire or deliveryCustomer
# deliveryCustomer = "deliveryCustomer"

# parameters = [
#     str(JSONFILE),
#     str(PYTHON_EXE),
#     str(PYTHON_MAIN_SCRIPT),
#     str(COMMENCE_WRAPPER),
# ]
