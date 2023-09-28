from pathlib import Path

from main import ShipDirection, ShipMode, ShipmentCategory, main

config, shipments = main(category=ShipmentCategory.HIRE, shipping_mode=ShipMode.SHIP,
                         direction=ShipDirection.OUT, file=Path('path/to/your/file.dbf'))

...
