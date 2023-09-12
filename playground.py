from dataclasses import asdict
from pathlib import Path
import datetime

from core.cmc_updater import PS_FUNCS, edit_commence
from core.config import Config, logger
from core.enums import ShipMode, ShipmentCategory, DateTimeMasks
from shipper.shipment import ShipmentInput
from shipper.shipper import Shipper, get_shipments


script = 'C:\paul\AmDesp\scripts\cmc_updater.ps1'
# in_file = r'E:\Dev\AmDesp\data\amherst_export.dbf'
in_file = Path(r'E:\Dev\AmDesp\data\rd_test_export.dbf')
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP


def do_commence():
    # record_name = shipment.shipment_name
    record_name = 'not very real is this'
    table_name = 'Hire'
    update_package = {
        # 'Name': 'Testing some more stuff',
        'To Customer': 'Test',
    }
    function_name = PS_FUNCS.OVERWRITE.value

    edit_commence(pscript="C:\paul\AmDesp\scripts\cmc_updater_funcs.ps1", function=function_name, table=table_name,
                  record=record_name, package=update_package)



def main():
    """mock env from input_file"""
    config = Config.from_toml(mode=ship_mode, outbound=outbound)
    shipper = Shipper(dbay_creds=config.dbay_creds)
    shipments = get_shipments(outbound=outbound, category=category, dbase_file=in_file, import_mappings=config.import_mappings)
    ...


if __name__ == '__main__':
    ...
    # main()
