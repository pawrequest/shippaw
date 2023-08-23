import datetime

from core.config import Config
from core.enums import ShipMode, ShipmentCategory

script = 'C:\paul\AmDesp\scripts\cmc_updater.ps1'
in_file = r'E:\Dev\AmDesp\data\rd_test_export.dbf'
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP
config = Config.from_toml(mode=ship_mode, outbound=outbound)

