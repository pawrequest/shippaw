# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces
# todo api rate limit avoidance?
# todo move from r drive to platform agnostic

import sys

from despatchbay.despatchbay_sdk import DespatchBaySDK

from amdesp_shipper.core.config import Config, get_amdesp_logger
from amdesp_shipper.gui.main_gui import MainGui
from amdesp_shipper.shipment import Shipment
from amdesp_shipper.shipper import Shipper


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
        shipments = Shipment.get_shipments(config=config)
        gui = MainGui(config=config, client=client)
        shipper = Shipper(config=config, client=client, gui=gui, shipments=shipments)
        shipper.dispatch()

    except Exception as e:
        logger.exception(f'MAINLOOP ERROR: {e}')


if __name__ == '__main__':
    # AmDesp called from commandline, i.e. launched from Commence vbs script - parse args for mode
    logger.info(f'launched with {len(sys.argv)} arguments:{sys.argv}')
    if len(sys.argv) > 1:
        shipping_mode = sys.argv[1].lower()
    else:
        shipping_mode = 'fake'
    main(main_mode=shipping_mode)