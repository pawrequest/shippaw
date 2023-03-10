import sys

from python.AmDespShipper import ShippingApp

def shipper(ship_mode, xmlfileloc=None):
    app = ShippingApp(ship_mode, xmlfileloc)
    app.prepare_shipment()
    app.process_shipment()
    return "returned from python"

def test():
    print("SOMETHNG")

if __name__ == '__main__':
    if len(sys.argv) >1:
        xmlfileloc = sys.argv[1]
    else:
        xmlfileloc = None
    shipper('sand', xmlfileloc=xmlfileloc)
    # test()
