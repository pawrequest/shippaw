import argparse
import sys

import PySimpleGUI as sg

from core.config import Config, logger
from core.enums import ShipmentCategory, ShipMode, ShipDirection
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
    while not args.input_file:
        args.input_file = sg.popup_get_file("Select input file")
    args.category = ShipmentCategory[args.category]
    outbound = 'out' == args.direction.lower()
    config = Config.from_toml(mode=args.shipping_mode, outbound=outbound)
    shipper = Shipper(config=config)
    shipper.get_shipments(category=args.category, dbase_file=args.input_file)

    if not shipper.shipments:
        logger.info('No shipments to process.')
        sys.exit()

    if args.shipping_mode == ShipMode.SHIP.name:
        shipper.dispatch()

    elif args.shipping_mode == ShipMode.TRACK.name:
        shipper.track()


    sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AmDesp Shipping Agent.")
    parser.add_argument('shipping_mode', choices=[mode.name for mode in ShipMode], help="Choose shipping mode.")
    parser.add_argument('direction', choices=[direc.name for direc in ShipDirection], help="Choose shipping direction.")
    parser.add_argument('category', choices=[category.name for category in ShipmentCategory],
                        help="Choose shipment category.")
    parser.add_argument('input_file', nargs='?', help="Path to input file.")
    args = parser.parse_args()
    logger.info(f'{args=}')
    main(args)
