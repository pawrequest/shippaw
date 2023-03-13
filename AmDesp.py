import sys

from python.AmDespShipper import ShippingApp

def shipper(ship_mode, xmlfile):
    app = ShippingApp(ship_mode)
    app.run(xmlfile)


def test():
    print("SOMETHNG")

if __name__ == '__main__':
    if len(sys.argv) >1:
        shipmode = sys.argv[1]
        xmlfile = sys.argv[2]
    else:
        shipmode = 'sand'
        xmlfile = 'C:\AmDesp\data\AmShip.xml'
    shipper(ship_mode=shipmode, xmlfile=xmlfile)
    # test()
