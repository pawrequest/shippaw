from despatchbay.despatchbay_sdk import DespatchBaySDK

from core.config import Config
from core.enums import ShipMode, ShipmentCategory
from core.funcs import log_shipment
from gui.main_gui import MainGui
from shipper.shipment import Shipment
from shipper.shipper import Shipper

shipping_mode = ShipMode.SHIP_OUT
category = ShipmentCategory.HIRE
input_file = r'E:\Dev\AmDesp\data\amherst_bulk_test.dbf'
log_path = 'bulk_test.json'

config = Config.from_toml2(mode=shipping_mode)
config.sandbox = True
creds = config.dbay_creds
client = DespatchBaySDK(api_user=creds.api_user, api_key=creds.api_key)
shipments = Shipment.get_shipments(config=config, category=category, dbase_file=input_file)
gui = MainGui(config=config, client=client)
shipper = Shipper(config=config, client=client, gui=gui, shipments=shipments)
shipper.prepare_shipments()
[log_shipment(shipment=shipment, log_path=log_path) for shipment in shipper.shipments]
