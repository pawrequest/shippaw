import argparse
import sys
from pathlib import Path

import PySimpleGUI as sg

from core.config import Config, logger
from core.enums import ShipmentCategory, ShipMode
from shipper.shipper import Shipper

"""
Amdesp - middleware to connect Commence RM to DespatchBay's shipping service.
includes
+ Commence vbs scripts for exporting records to xml,
+ python app with pysimplegui gui
+ powershell to check vbs into commence
+ powershell to log shipment ids to commence
+ Vovin CmcLibNet installer bundled for logging to Commence
"""

def main(args):
    while not Path(args.input_file).exists():
        args.input_file = sg.popup_get_file("Select input file")

    config = Config.from_toml(mode=args.shipping_mode)
    shipper = Shipper(config=config)
    shipper.get_shipments(category=args.category, dbase_file=args.input_file)

    if args.shipping_mode in [ShipMode.SHIP_OUT.name, ShipMode.SHIP_IN.name]:
        shipper.dispatch()

    elif args.shipping_mode == ShipMode.TRACK.name:
        shipper.track()


    sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AmDesp Shipping Agent.")
    parser.add_argument('shipping_mode', choices=[mode.name for mode in ShipMode], help="Choose shipping mode.")
    parser.add_argument('category', choices=[category.name for category in ShipmentCategory],
                        help="Choose shipment category.")
    parser.add_argument('input_file', nargs='?', help="Path to input file.")
    args = parser.parse_args()
    logger.info(f'{args=}')
    main(args)
