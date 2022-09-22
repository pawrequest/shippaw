import os
import pathlib

from python.despatchbay.despatchbay_sdk import DespatchBaySDK

####  CONFIG PATHS HERE ########
ROOT_DIR = pathlib.Path("/")

sender_id = "5536"  # should be env var?
API_USER = os.getenv("DESPATCH_API_USER")
API_KEY = os.getenv("DESPATCH_API_KEY")
DATA_DIR = ROOT_DIR / "shipmentJson"
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
PYTHON_EXE = ROOT_DIR / "python" / "bin" / "python.exe"
PYTHON_MAIN_SCRIPT = ROOT_DIR / "main.py"
COMMENCE_WRAPPER = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
JSONFILE = DATA_DIR / "AmShip.json"
JsonPath = str(JSONFILE)
XMLFILE = DATA_DIR / "AmShip.xml"
LOGFILE = (DATA_DIR / "AmLog.json")
client = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
sender = client.sender(address_id=sender_id)
courier_id = 8  # parcelforce
pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)  # make the shipmentJson dirs

line = '-' * 100
# com_cols_lower = {'delivery tel': 'phone', 'delivery email': 'email', 'delivery address': 'address',
#             'send out date': 'send date', 'delivery postcode': 'postcode', 'reference number': 'hire ref',
#             "deliv name": "customer", "deliv address": "address", "deliv contact": "contact", "deliv email": "email",
#             "deliv postcode": "postcode", "deliv telephone": "tel"}

# new_com = {key.title(): value for (key, value) in com_cols.items()}

com_fields = {'Delivery Tel': 'phone', 'Delivery Email': 'email', 'Delivery Address': 'address', 'Send Out Date': 'send date',
     'Delivery Postcode': 'postcode', 'Reference Number': 'hire ref', 'Deliv Name': 'customer',
     'Deliv Address': 'address', 'Deliv Contact': 'contact', 'Deliv Email': 'email', 'Deliv Postcode': 'postcode',
     'Deliv Telephone': 'tel'}
export_exclude_keys = ["addressObject", "date_object", 'service_object', 'services', 'parcels', 'shipment_return']
field_fixes = {}


#  other fields
is_shipped = "is collection booked"
added_shipment = "despatch added shipment"
building_num = "building num"
address_firstline = "address first line"
searchterm = "search term"
shipnum = "shipment number"
shipping_service_id = "shipment service id"
shipping_service_name = "shipping service name"
shipping_cost = "shipping cost"
desp_shipment_id = "despatch id"
candidates = "candidates"
date_check = "date check"
category = "category"  # hire or customer
customer = "customer"

parameters = [
    str(JSONFILE),
    str(PYTHON_EXE),
    str(PYTHON_MAIN_SCRIPT),
    str(COMMENCE_WRAPPER),
]
