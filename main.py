import argparse
import sys
from pathlib import Path
from typing import List

import PySimpleGUI as sg

from core.config import Config, logger
from core.enums import ShipDirection, ShipMode, ShipmentCategory
from core.funcs import is_connected
from shipper.shipment import ShipmentInput
from shipper.shipper import Shipper, dispatch, get_shipments

"""
Amdesp - middleware to connect Commence RM to DespatchBay's shipping service.
includes
+ Commence vbs scripts for exporting records to xml,
+ python app with pysimplegui gui
+ powershell to check vbs into commence
+ wraps Vovin CmcLibNet to update commence database - installer bundled 
"""


def initial_checks():
    is_internet_connected = is_connected()


def main(args):
    initial_checks()
    outbound = 'out' == args.direction.value.lower()
    config = Config.from_toml(mode=args.shipping_mode, outbound=outbound)
    shipper = Shipper(dbay_creds=config.dbay_creds)

    shipments: List[ShipmentInput] = get_shipments(category=args.category, dbase_file=args.input_file,
                                                   import_mappings=config.import_mappings, outbound=outbound)

    if not shipments:
        logger.info('No shipments to process.')
        sys.exit()

    if args.shipping_mode == ShipMode.SHIP:
        dispatch(config=config, shipments=shipments)

    elif args.shipping_mode == ShipMode.TRACK:
        shipper.track()

    sys.exit(0)


if __name__ == '__main__':
    mode_choices = [mode.name for mode in ShipMode]
    category_choices = [category.name for category in ShipmentCategory]
    direction_choices = [direc.name for direc in ShipDirection]

    parser = argparse.ArgumentParser(description="AmDesp Shipping Agent.")

    parser.add_argument('--mode', choices=mode_choices,
                        help="Choose shipping mode.")
    parser.add_argument('--category', choices=category_choices,
                        help="Choose shipment category.")
    parser.add_argument('--direction', choices=direction_choices,
                        help="Choose shipping direction.")
    parser.add_argument('--input_file', type=Path, help="Path to .dbf input file.")
    args = parser.parse_args()

    args.category = ShipmentCategory[args.category]
    args.shipping_mode = ShipMode[args.mode]
    args.direction = ShipDirection[args.direction]
    while not args.input_file:
        args.input_file = Path(sg.popup_get_file("Select input file"))
    logger.info(f'{args=}')

    main(args)
