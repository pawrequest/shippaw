from core.config import Config
from core.enums import ShipmentCategory, ShipMode
from core.funcs import update_commence
from shipper.shipper import Shipper

in_file = r'C:\paul\AmDesp\data\test_hire.dbf'
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP


def playground(shipment, config):
    """test stuff here"""
    # # update a record
    update_package = {'Missing Kit': 'withshelll'}
    update_commence(update_package=update_package, table_name='Hire', record_name=shipment.shipment_name,
                    script_path=config.paths.cmc_updater_append, with_shell=False)

    # # # insert a record
    # update_package = {'Notes' : 'some notes'}
    # update_commence_shell(update_package=update_package, table_name='Customer', record_name='test python',
    #                 script_path=r'C:\paul\AmDesp\scripts\cmc_updater_insert.ps1')
    # # insert a record
    # update_package = {'Notes' : 'some notes'}
    # update_commence_aggy(update_package=update_package, table_name='Customer', record_name='test python',
    #                 script_path=r'C:\paul\AmDesp\scripts\cmc_updater_insert.ps1', with_shell=False)
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
