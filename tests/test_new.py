from pathlib import Path

from src.desp_am.core.entities import ShipmentCategory, ShipMode, ShipDirection
from src.desp_am.gui.main_gui import post_book
from src.desp_am.main import main
from src.desp_am.shipper.ship import dispatch_gui


# def test_new():
#     category = ShipmentCategory.HIRE
#     config, client, shipments = main(category=category, shipping_mode=mode, direction=direction, file=file_in)
#     completed = dispatch_gui(config=config, shipment_dict=shipments, client=client)
#     post_book(shipment_dict=completed)
#     ...
#
#     ...


def test_ship2():
