# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces
# todo api rate limit avoidance?
# todo move from r drive to platform agnostic

import sys

from despatchbay.despatchbay_sdk import DespatchBaySDK

from core.config import Config, get_amdesp_logger
from core.enums import ShipmentCategory, ShipMode
from gui.main_gui import MainGui
from shipper.shipment import Shipment, get_dbay_shipments, DbayShipment
from shipper.shipper import Shipper

"""
Amdesp - middleware to connect Commence RM to DespatchBay's shipping service.
modes = [ship_in, ship_out, track_in, track_out]
takes xml and (soon) dbase files as inputs - location provided as argument
validates and corrects data to conform to shipping service requirements,
allows user to update addresses / select shipping services etc, queue and book collection,
prints labels, gets tracking info on existing shipments
includes
+ Commence vbs scripts for exporting xml,
+ python app with pysimplegui gui
+ powershell to check vbs into commence
+ powershell to log shipment ids to commence
+ Vovin CmcLibNet installer for interacting with commence
"""

logger = get_amdesp_logger()


def main(main_mode: str):
    config = Config.from_toml2(mode=main_mode)
    client = DespatchBaySDK(api_user=config.dbay_creds.api_user, api_key=config.dbay_creds.api_key)
    shipments = Shipment.get_shipments(config=config, category=category, dbase_file=input_file_arg)
    shipments_dict = get_dbay_shipments(import_mapping=config.import_mapping, category=category,
                                        dbase_file=input_file_arg)
    gui = MainGui(outbound=config.outbound, sandbox=config.sandbox)
    shipper = Shipper(config=config, client=client, gui=gui, shipments=shipments, shipments_dict=shipments_dict)
    if main_mode == 'drop':
        shipper.dispatch_outbound_dropoffs()
    if 'ship' in main_mode:
        shipper.dispatch()
    elif 'track' in main_mode:
        shipper.track()
    sys.exit()


if __name__ == '__main__':
    logger.info(f'launched with {len(sys.argv)} arguments:{sys.argv}')
    shipping_mode_arg = sys.argv[1]
    category_arg = sys.argv[2]
    input_file_arg = sys.argv[3]

    category = ShipmentCategory[category_arg]
    shipping_mode = ShipMode[shipping_mode_arg]

    main(main_mode=shipping_mode)
