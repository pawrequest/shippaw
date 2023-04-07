# todo updates commence when shipment delivered
# imports in-range shipments to batch process
import pathlib
import sys

import platformdirs

from amdesp.config import Config
from amdesp.gui_layouts import tracking_viewer_window
from amdesp.shipper import App, get_shipments # , get_sender_recip

root_dir = pathlib.Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
STORED_XML = str(root_dir / 'data' / 'amship.xml')

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


def main():
    """ sandbox = fake shipping client, no money for labels!"""
    config = Config()
    client = config.get_dbay_client(sandbox=SANDBOX)
    app = App()
    shipments = get_shipments(config=config, in_file=in_file)


    for shipment in shipments:
        if 'ship' in mode:
            if 'in' in mode:
                shipment.is_return = True
            app.main_loop(client=client, config=config, sandbox=SANDBOX, shipment=shipment)
        elif 'track' in mode:
            if 'in' in mode:
                try:
                    tracking_viewer_window(shipment_id=shipment.inbound_id, client=client)
                except:
                    ...
                    # sg.popup_error("No Shipment ID")

            elif 'out' in mode:
                try:
                    tracking_viewer_window(shipment.outbound_id, client=client)
                except:
                    ...
                    # sg.popup_error("No Shipment ID")


if __name__ == '__main__':
    # AmDesp called from commandline, i.e launched from Commence vbs script - parse args for mode
    if len(sys.argv) > 1:
        print(sys.argv)
        mode = sys.argv[1]
        in_file = sys.argv[2]
        SANDBOX = False

    # AmDesp called from IDE, set mode synthetically:
    else:
        in_file = STORED_XML
        SANDBOX = True

        mode = 'ship_out'
        # mode = 'track_in'

    main()
