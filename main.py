# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces
# todo api rate limit avoidance?
# todo move from r drive to platform agnostic

import sys

import PySimpleGUI as sg

from amdesp.config import Config, get_amdesp_logger
from amdesp.gui import MainGui
from amdesp.shipment import Shipment
from amdesp.shipper import Shipper


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
    """ sandbox = fake shipping client, no money for labels!"""
    sg.popup_quick_message('Config', keep_on_top=True)
    try:

        config = Config.from_toml2(mode=main_mode)
        client = config.setup_dbay()
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
        mode = sys.argv[1].lower()
    else:
        mode = 'fake'
    main(main_mode=mode)
