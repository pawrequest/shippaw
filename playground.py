from pathlib import Path

from src.desp_am.core.cmc_updater import PS_FUNCS, edit_commence
from src.desp_am.core.entities import ShipMode, ShipmentCategory

script = 'C:\paul\AmDesp\scripts\cmc_updater.ps1'
# in_file = r'E:\Dev\AmDesp\data\amherst_export.dbf'
# in_file = Path(r'C:\paul\AmDesp\data\amherst_export_sale.dbf')
in_file = Path(r'data/amherst_export_sale.dbf')
outbound = True
category = ShipmentCategory.SALE
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

#
# def main():
#     """mock env from input_file"""
#     new_conf = get_config(outbound=outbound, category=category)
#     establish_client(dbay_creds=new_conf.dbay_creds)
#
#     # shipments = get_shipments(outbound=outbound, category=category, dbase_file=in_file, import_map=new_conf.import_map)
#     records = records_from_dbase(dbase_file=in_file)
#     shipments = shipments_from_records(category=category, import_map=new_conf.import_map, outbound=outbound,
#                                        records=records)
#     ...


if __name__ == '__main__':
    # main()
    ...