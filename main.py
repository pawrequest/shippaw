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



# todo changing shipment name breaks logging to commence

# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces
import os
from pathlib import Path
import sys

import platformdirs

from amdesp.config import Config, get_amdesp_logger
from amdesp.shipper import Shipper
import PySimpleGUI as sg
import logging

# sandbox switch for non CLI:
SANDBOX = True

# get stored data files for non CLI
ROOT_DIR = Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
# STORED_XML = str(ROOT_DIR / 'data' / 'amship.xml')
STORED_XML = r'c:\amdesp\data\amship.xml'
# STORED_DBASE = str(ROOT_DIR / 'data' / 'hire_in_range_bulk.dbf')
STORED_DBASE = str(ROOT_DIR / 'data' / 'single_hire.dbf').lower()
# STORED_DBASE = r'E:\Dev\AmDesp\data\all_hires.DBF'
#


# INPUT_FILE = STORED_XML
INPUT_FILE = STORED_DBASE
logger = get_amdesp_logger()


def main(main_mode: str, main_sandbox: bool, infile: str):
    """ sandbox = fake shipping client, no money for labels!"""
    sg.popup_quick_message('Config', keep_on_top=True)
    try:
        root_dir = Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
        config = Config.from_toml2(sandbox=main_sandbox, root_dir=root_dir)
        config.log_config()
        client = config.get_dbay_client_ag(config.dbay)
        shipper = Shipper(config=config)
        shipper.dispatch(mode=main_mode, client=client, in_file=infile)

    except Exception as e:
        ...


if __name__ == '__main__':
    # AmDesp called from commandline, i.e launched from Commence vbs script - parse args for mode
    logging.info(f'launched with arguments:{sys.argv}')
    if len(sys.argv) > 1:
        [logger.info(f'CONFIG - {arg + os.linesep}') for arg in sys.argv]
        mode = sys.argv[1]
        in_file = sys.argv[2]
        sandbox = False

    # AmDesp called from IDE - inject mode
    else:
        in_file = INPUT_FILE
        sandbox = SANDBOX
        mode = 'ship_out'
        # mode = 'track_in'

    main(main_mode=mode, infile=in_file, main_sandbox=sandbox)
