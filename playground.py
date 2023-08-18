from core.config import Config
from core.enums import ShipmentCategory, ShipMode
from core.funcs import update_commence, update_commence_shell
from shipper.shipper import Shipper

in_file = r'C:\paul\AmDesp\data\test_hire.dbf'
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP


def playground(shipment, config):
    """test stuff here"""
    # # update a record
    # update_package = {'Missing Kit': 'test2323'}
    # update_commence(update_package=update_package, table_name='Hire', record_name=shipment.shipment_name,
    #                 script_path=config.paths.cmc_updater_add)

    # # insert a record
    update_package = {'Notes' : 'some notes'}
    update_commence_shell(update_package=update_package, table_name='Customer', record_name='test python',
                    script_path=r'C:\paul\AmDesp\scripts\commence_updater_insert.ps1')
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
