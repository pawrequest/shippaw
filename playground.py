from core.config import Config
from core.enums import ShipmentCategory, ShipMode
from core.funcs import update_commence
from shipper.shipper import Shipper

in_file = r'C:\paul\AmDesp\data\amherst_export_test_bak.dbf'
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP


def playground(shipment, config):
    """test stuff here"""
    update_package = {'Missing Kit': 'Fake Text test', 'DB label printed': True}
    update_commence(update_package=update_package, table_name='Hire', record_name=shipment.shipment_name,
                    script_path=config.paths.cmc_updater_add)

    ...


def main():
    """mock env from input_file"""
    config = Config.from_toml(mode=ship_mode, outbound=outbound)
    shipper = Shipper(config=config)
    shipper.get_shipments(category=category, dbase_file=in_file)
    playground(shipment=shipper.shipments[0], config=config)

if __name__ == '__main__':
    main()
