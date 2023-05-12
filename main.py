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
from shipper.shipment import Shipment
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
    try:
        config = Config.from_toml2(mode=main_mode)
        creds = config.dbay_creds
        client = DespatchBaySDK(api_user=creds.api_user, api_key=creds.api_key)
        shipments = Shipment.get_shipments(config=config, category=category, dbase_file=input_file_arg)
        gui = MainGui(config=config, client=client)
        shipper = Shipper(config=config, client=client, gui=gui, shipments=shipments)
        shipper.dispatch()

    except Exception as e:
        logger.exception(f'MAINLOOP ERROR: {e}')


if __name__ == '__main__':
    # AmDesp called from commandline, i.e. launched from Commence vbs script - parse args for mode
    logger.info(f'launched with {len(sys.argv)} arguments:{sys.argv}')
    if len(sys.argv) > 1:
        shipping_mode_arg = sys.argv[1]
        category_arg = sys.argv[2]
        input_file_arg = sys.argv[3]

        try:
            category = ShipmentCategory[category_arg]
        except KeyError:
            logger.exception(f'invalid category argument: {category_arg}')
            raise
        try:
            shipping_mode = ShipMode[shipping_mode_arg]
        except KeyError:
            logger.exception(f'invalid mode argument: {shipping_mode_arg}')
            raise

    else:
        shipping_mode = ShipMode['FAKE']
        category = ShipmentCategory['FAKE']
        input_file_arg = 'fake'

    main(main_mode=shipping_mode)
