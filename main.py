import argparse
import sys

import PySimpleGUI as sg

from core.config import Config
from core.enums import ShipmentCategory, ShipMode
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


# def main(main_mode: str):
#     config = Config.from_toml(mode=main_mode)
#     shipper = Shipper(config=config)
#     shipments = shipper.get_shipments(config=config, category=category, dbase_file=input_file_arg)
#
#     if 'ship' in main_mode:
#         shipper.dispatch(config=config, shipments=shipments)
#
#     elif 'track' in main_mode:
#         ...
#
#     sys.exit()
#
#
# if __name__ == '__main__':
#     logger.info(f'launched with {len(sys.argv)} arguments:{sys.argv}')
#     shipping_mode_arg = sys.argv[1]
#     category_arg = sys.argv[2]
#     input_file_arg = sys.argv[3]
#
#     category = ShipmentCategory[category_arg]
#     shipping_mode = ShipMode[shipping_mode_arg]
#
#     main(main_mode=shipping_mode)

def main():
    parser = argparse.ArgumentParser(description="AmDesp Shipping Agent.")
    parser.add_argument('shipping_mode', choices=[mode.name for mode in ShipMode], help="Choose shipping mode.")
    parser.add_argument('category', choices=[category.name for category in ShipmentCategory],
                        help="Choose shipment category.")
    # parser.add_argument('input_file', help="Path to input file.")
    parser.add_argument('input_file', nargs='?', help="Path to input file.")

    args = parser.parse_args()

    while not args.input_file:
        args.input_file = sg.popup_get_file("Select input file")

    config = Config.from_toml(mode=args.shipping_mode)
    shipper = Shipper(config=config)
    shipper.get_shipments(category=args.category, dbase_file=args.input_file)

    if args.shipping_mode in [ShipMode.SHIP_OUT.name, ShipMode.SHIP_IN.name]:
        shipper.dispatch()

    elif args.shipping_mode == ShipMode.TRACK:
        # Implement the logic for the 'track' mode.
        pass

    sys.exit()


if __name__ == '__main__':
    main()
