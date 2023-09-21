import argparse
import sys
from pathlib import Path

from core.config import CONFIG_TOML, config_from_dict, get_config_dict
from core.logger import amdesp_logger
from core.dbay_client import get_dbay_client
from core.enums import ShipDirection, ShipMode, ShipmentCategory
from core.funcs import is_connected
from gui.main_gui import post_book
from shipper.shipment import shipments_from_file
from shipper.shipper import dispatch_gui_dict, prepare_batch, ship_list_to_dict

"""
Amdesp - middleware to connect Commence RM to DespatchBay's shipping service.
includes
+ Commence vbs scripts for exporting records to xml,
+ python app with pysimplegui gui
+ powershell to check vbs into commence
+ wraps Vovin CmcLibNet to update commence database - installer bundled 
"""



def intitial_config(category: ShipmentCategory):
    is_connected()
    config = config_from_dict(get_config_dict(toml_file=CONFIG_TOML))
    client = get_dbay_client(creds=config.dbay_creds)
    import_map = config.import_mappings[category.name.lower()]
    return config, client, import_map

def main(category: ShipmentCategory, shipping_mode: ShipMode, direction: ShipDirection, file: Path):
    outbound = direction == ShipDirection.OUT
    config, client, import_map = intitial_config(category=category)
    shipments = shipments_from_file(category, file, import_map, outbound)
    shipments_prepared = prepare_batch(shipments=shipments, client=client, config=config)
    dicty = ship_list_to_dict(shipments=shipments_prepared)

    if __name__ == '__main__':
        if shipping_mode == ShipMode.SHIP:
            # completed = dispatch_gui(config=config, shipments=shipments_prepared, client=client)
            completed = dispatch_gui_dict(config=config, shipment_dict=dicty, client=client)
            post_book(shipments=completed)
            # dispatch(config=config, prepared_shipments=shipments_prepared, client=client)

        sys.exit(0)
    else:
        return config, shipments


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
    parser.add_argument('--file', type=Path, help="Path to .dbf input file.")

    args = parser.parse_args()

    args.category = ShipmentCategory[args.category]
    args.shipping_mode = ShipMode[args.mode]
    args.direction = ShipDirection[args.direction]
    args.file = Path(args.file)

    amdesp_logger.debug(f'{args=}')

    main(category=args.category,
         shipping_mode=args.shipping_mode,
         direction=args.direction,
         file=args.file)
