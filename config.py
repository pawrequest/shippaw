import os
import pathlib

from python.despatchbay_sdk import DespatchBaySDK

sender_id = "5536"  # should be env var?
API_USER = os.getenv("DESPATCH_API_USER")
API_KEY = os.getenv("DESPATCH_API_KEY")
ROOT_DIR = pathlib.Path("C:\AmDesp")
DATA_DIR = ROOT_DIR / "data"
LABEL_DIR = DATA_DIR / "Parcelforce Labels"
PYTHON_EXE = ROOT_DIR / "python" / "bin" / "python.exe"
PYTHON_MAIN_SCRIPT = ROOT_DIR / "main.py"
COMMENCE_WRAPPER = "C:\Program Files\Vovin\Vovin.CmcLibNet\Vovin.CmcLibNet.dll"
JSONFILE = DATA_DIR / "AmShip.json"
LOGFILE = (DATA_DIR / "AmLog.json")
client = DespatchBaySDK(api_user=API_USER, api_key=API_KEY)
sender = client.sender(address_id=sender_id)
courier_id = 8  # parcelforce
pathlib.Path(LABEL_DIR).mkdir(parents=True, exist_ok=True)  # make the data dirs

cols_hire = ["To Customer", "Send Out Date", "Delivery Postcode", "Delivery Address", "Delivery Name",
                      "Delivery tel", "Delivery Email", "Boxes", "Reference Number", "Delivery Contact"]


cols_sale = ["Deliv Name", "Deliv Address", "Deliv Contact", "Deliv Email", "Deliv Postcode", "Deliv Telephone"]


# Commence Column Names
hire_customer = "To Customer"
phone = "Delivery Tel"
email = "Delivery Email"
address = "Delivery Address"
boxes = "Boxes"
send_date = "Send Out Date"
postcode = "Delivery Postcode"
hire_ref = "Reference Number"
shipment_id = "Shipment_id"
delivery_contact = "Delivery Contact"
delivery_name = "Delivery Name"

# Despatchbay object fields
service_object = "Shipping Service Object"
date_object = "Date Object"
address_object = "Address Object"
despatch_shipped_object = "Despatch Shipped Object"

#  other fields
is_shipped = "Is Shipped"
added_shipment = "Despatch Added Shipment"
building_num = "Building Num"
address_firstline = "Address First Line"
searchterm = "Search Term"
shipnum = "Shipment Number"
shipping_service_id = "Shipment Service ID"
shipping_service_name = "Shipping Service Name"
shipping_cost = "Shipping Cost"
desp_shipment_id = "Despatch ID"
candidates = "Candidates"
date_check = "date_check"
category = "Category"  # Hire or Customer

parameters = [
    str(JSONFILE),
    str(PYTHON_EXE),
    str(PYTHON_MAIN_SCRIPT),
    str(COMMENCE_WRAPPER),

]
