import sys

from python.AmDespShipper import ShippingApp

def shipper(ship_mode, xmlfileloc=None):
    app = ShippingApp(ship_mode, xmlfileloc)
    app.run()

def test():
    print("SOMETHNG")

if __name__ == '__main__':
    if len(sys.argv) >1:
        shipmode = sys.argv[1]
        xmlfileloc = sys.argv[2]
    else:
        shipmode = 'sand'
        xmlfileloc = None
    shipper(ship_mode=shipmode, xmlfileloc=xmlfileloc)
    # test()
