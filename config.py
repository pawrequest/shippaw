import os
import pathlib

from python.despatchbay_sdk import DespatchBaySDK

####  CONFIG PATHS HERE ########
ROOT_DIR = pathlib.Path("C:\AmDesp")

sender_id = "5536"  # should be env var?
API_USER = os.getenv("DESPATCH_API_USER")
API_KEY = os.getenv("DESPATCH_API_KEY")
DATA_DIR = ROOT_DIR / "data"
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
PYTHON_EXE = ROOT_DIR / "python" / "bin" / "python.exe"
PYTHON_MAIN_SCRIPT = ROOT_DIR / "main.py"
COMMENCE_WRAPPER = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
JSONFILE = DATA_DIR / "AmShip.json"
XMLFILE = DATA_DIR / "AmShip.xml"
LOGFILE = (DATA_DIR / "AmLog.json")
client = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
sender = client.sender(address_id=sender_id)
courier_id = 8  # parcelforce
pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)  # make the data dirs

cols_hire = ["To Customer", "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery Name",
             "Delivery tel", "Delivery Email", "Boxes", "Reference Number", "Delivery Contact"]

cols_sale = ["Deliv Name", "Deliv Address", "Deliv Contact", "Deliv Email", "Deliv Postcode", "Deliv Telephone"]
new_sales= {}
for i in cols_sale:
    new_sales



# commence_columns = {'delivery tel': 'phone', 'delivery email': 'email', 'delivery address': 'address', 'boxes': 'boxes',
#  'send out date': 'send_date', 'delivery postcode': 'postcode', 'reference number': 'hire_ref',
#  'shipment_id': 'shipment_id', 'delivery contact': 'delivery_contact', 'delivery name': 'delivery_name','delivery cost':'shipping_charged'}

commence_columns = {'delivery_tel': 'phone', 'delivery_email': 'email', 'delivery_address': 'address',
 'send_out_date': 'send_date', 'delivery_postcode': 'postcode', 'reference_number': 'hire_ref'}

export_exclude_keys = ["address_object", "date_object", 'service_object', 'services', 'parcels', 'shipment_return']

# # Commence Column Names
# # hire_customer = "To Customer"
# phone = "Delivery Tel"
# email = "Delivery Email"
# address = "Delivery Address"
# boxes = "Boxes"
# send_date = "Send Out Date"
# postcode = "Delivery Postcode"
# hire_ref = "Reference Number"
# shipment_id = "Shipment_id"
# delivery_contact = "Delivery Contact"
# delivery_name = "Delivery Name"

# Despatchbay object fields
# service_object = "Shipping Service Object"
# date_object = "Date Object"
# address_object = "Address Object"
# despatch_shipped_object = "Despatch Shipped Object"

#  other fields
is_shipped = "is collection_booked"
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
date_check = "date_check"
category = "category"  # hire or customer
customer = "customer"

parameters = [
    str(JSONFILE),
    str(PYTHON_EXE),
    str(PYTHON_MAIN_SCRIPT),
    str(COMMENCE_WRAPPER),

]
