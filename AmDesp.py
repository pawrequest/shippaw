import sys
import os
from py_code.AmDespShipper import ShippingApp


def shipper(ship_mode, xmlfile):
    app = ShippingApp(ship_mode)
    app.run(xmlfile)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        shipmode = sys.argv[1]
        xmlfile = sys.argv[2]
    else:
        shipmode = 'sand'
        xmlfile = 'C:\AmDesp\data\AmShip.xml'
    shipper(ship_mode=shipmode, xmlfile=xmlfile)

# todo [mobility] - repo on ryzen is e/dev/, at amherst is c/paul ... use c/pss on both / all systems? or home?
# todo package imports / sys.path etc. amdesp.spec[pathex].now = e/dev
