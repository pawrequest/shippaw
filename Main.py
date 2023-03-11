import sys

from python.AmDespShipper import ShippingApp

def shipper(ship_mode, xmlfileloc=None):
    app = ShippingApp(ship_mode, xmlfileloc)
    if app.prepare_shipment():
        if app.process_shipment():
            app.log_json()
            app.log_tracking()

def test():
    print("SOMETHNG")

if __name__ == '__main__':
    if len(sys.argv) >1:
        xmlfileloc = sys.argv[1]
    else:
        xmlfileloc = None
    shipper('sand', xmlfileloc=xmlfileloc)
    # test()
