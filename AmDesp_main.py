import sys
# import pathlib
# cwd=str(pathlib.Path.cwd())
# print(f"{cwd=}")
# sys.path.append(cwd)
# # from .AmDesp_python.AmDespShipper import ShippingApp
from .AmDesp_python.AmDespShipper import ShippingApp

def shipper(ship_mode, xmlfileloc=None):
    app = ShippingApp(ship_mode, xmlfileloc)
    app.run()


if __name__ == '__main__':
    if len(sys.argv) >1:
        xmlfileloc = sys.argv[1]
        # print(f"{xmlfileloc=}")
    else:
        xmlfileloc = None
    shipper('sand', xmlfileloc=xmlfileloc)
