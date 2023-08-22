from datetime import datetime

from core.cmc_updater import update_commence, PS_FUNCS, edit_commence
from core.config import Config
from core.enums import ShipmentCategory, ShipMode, DateTimeMasks
from shipper.shipper import Shipper
script = 'C:\paul\AmDesp\scripts\cmc_updater.ps1'
aggy_script = r'C:\paul\AmDesp\scripts\cmc_updater.ps1'
in_file = r'C:\paul\AmDesp\data\test_hire.dbf'
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP


def playground(shipment, config: Config):
    """test stuff here"""
    record_name = "Test - 16/08/2023 ref 31619"
    # record_name = "Test"
    table_name = 'Hire'
    update_package = {
        'Missing Kit': f'nothing to see',
    }

    edit_commence(pscript="C:\paul\AmDesp\scripts\cmc_updater_funcs.ps1", function=PS_FUNCS.OVERWRITE.value, table=table_name, record=record_name, package=update_package)

    # # update_commence(update_package=update_package, table_name='Hire', record_name=shipment.shipment_name,
    # #                 script_path=config.paths.cmc_updater_append, with_shell=False)
    #
    # update_commence(update_package=update_package, table_name=table_name, record_name=record_name,
    #                 script_path=script, append=False, insert=False)

    # # insert a record
    # update_package = {'Notes' : 'some notes'}
    # update_commence(update_package=update_package, table_name='Customer', record_name='test python',
    #                 script_path=r'C:\paul\AmDesp\scripts\cmc_updater.ps1', insert=True)

    # # insert a record
    # update_package = {'Notes' : 'some notes'}
    # update_commence_aggy(update_package=update_package, table_name='Customer', record_name='test python',
    #                 script_path=r'C:\paul\AmDesp\scripts\cmc_updater_insert.ps1', with_shell=True)
    #
    ...


def main():
    """mock env from input_file"""
    config = Config.from_toml(mode=ship_mode, outbound=outbound)
    shipper = Shipper(config=config)
    shipper.get_shipments(category=category, dbase_file=in_file)
    playground(shipment=shipper.shipments[0], config=config)


if __name__ == '__main__':
    main()
