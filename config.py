import os, pathlib
from python.despatchbay_sdk import DespatchBaySDK
import sys

ROOT_DIR = pathlib.Path("C:\AmDesp")

sender_id = '5536'  # should be env var?
API_USER = os.getenv('DESPATCH_API_USER')
API_KEY = os.getenv('DESPATCH_API_KEY')


DATA_DIR = ROOT_DIR / 'data'
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
PYTHON_EXE = ROOT_DIR / 'bin' / 'python.exe'
PYTHON_MAIN_SCRIPT = ROOT_DIR / 'main.py'
COMMENCE_WRAPPER = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"

pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)  # make the data dirs
JSONFILE = pathlib.Path(DATA_DIR / "AmShip.json")
LOGFILE = pathlib.Path(DATA_DIR / 'AmLog.json')
client = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
sender = client.sender(address_id=sender_id)
courier_id = 8  # parcelforce

cols_from_commence_hire = ["To Customer", "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery Name",
                      "Delivery tel", "Delivery Email", "Boxes", "Reference Number", "Delivery Contact"]

# Commence Column Names
customer_field = 'To Customer'
phone_field = 'Delivery Tel'
email_field = 'Delivery Email'
address_field = 'Delivery Address'
boxes_field = 'Boxes'
send_date_field = 'Send Out Date'
postcode_field = 'Delivery Postcode'
hire_ref_field = 'Reference Number'
shipment_id_field = 'Shipment_id'
delivery_contact_field = "Delivery Contact"
delivery_name_field = "Delivery Name"

# Despatchbay object fields
despatch_shipped_object_field = "Despatch Shipped Object"
service_object_field = 'Shipping Service Object'
date_object_field = "Date Object"
address_object_field = 'Address Object'

#  other fields
is_shipped_field = "Is Shipped"
added_shipment_field = "Despatch Added Shipment"
building_num_field = 'Building Num'
address_firstline_field = 'Address First Line'
searchterm_field = 'Search Term'
shipnum_field = 'Shipment Number'
shipping_service_id_field = "Shipment Service ID"
shipping_service_name_field = "Shipping Service Name"
shipping_cost_field = "Shipping Cost"
desp_shipment_id_field = "Despatch ID"
candidates_field = 'Candidates'

parameters = [
    str(JSONFILE),
    str(PYTHON_EXE),
    str(PYTHON_MAIN_SCRIPT),
    str(COMMENCE_WRAPPER),

]
