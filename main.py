# todo updates commence when shipment delivered
# todo tests
# todo better logging
# todo async / multiproces

import pathlib
import sys
from typing import Literal

import platformdirs

from amdesp.config import Config
from amdesp.shipper import App
from amdesp.shipment import Shipment
import PySimpleGUI as sg

root_dir = pathlib.Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
STORED_XML = str(root_dir / 'data' / 'amship.xml')
# STORED_DBASE = str(root_dir / 'data' / 'hire_in_range_bulk.dbf')
STORED_DBASE = str(root_dir / 'data' / 'single_hire.dbf')
# STORED_DBASE = r'C:\Users\giles\AppData\Local\pss\AmDesp\data\single_hire.DBF'

SANDBOX = None

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

# todo Literal typehint throwing warnings? mode:Literal['ship_in', 'ship_out', 'track_in','track_out']

def main(mode:str):
    """ sandbox = fake shipping client, no money for labels!"""
    config = Config()
    config.sandbox = SANDBOX
    client = config.get_dbay_client()
    outbound_shipments = Shipment.get_shipments(config=config, in_file=in_file)
    app = App()
    if mode == 'ship_out':
        app.go_ship_out(shipments=outbound_shipments,config=config, client=client)
    else:
        sg.popup_error(f"Mode Fault: {mode}")


if __name__ == '__main__':
    # AmDesp called from commandline, i.e launched from Commence vbs script - parse args for mode
    if len(sys.argv) > 1:
        print(sys.argv)
        mode = sys.argv[1]
        in_file = sys.argv[2]
        SANDBOX = False

    # AmDesp called from IDE, set mode synthetically:
    else:
        # in_file = STORED_XML
        in_file = STORED_DBASE
        SANDBOX = False
        mode = 'ship_out'
        # mode = 'track_in'

    main(mode=mode)
