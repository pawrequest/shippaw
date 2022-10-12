import sys

from python.AmDespProgrammer import ProgrammingAssistant
from python.AmDespShipper import ShippingApp


def shipper(ship_mode, xmlfile):
    app = ShippingApp(ship_mode, xmlfile)

    app.xml_to_shipment()
    if app.queue_shipment():
        if app.book_collection():
            print("success")
    app.log_json()


def programmer():
    prog = ProgrammingAssistant()
    prog.BootUp()
    prog.ProgramBatch()
    ...


def test():
    print("SOMETHNG")


if __name__ == '__main__':
    if any(".xml" in arg for arg in sys.argv):
        xmlfile = sys.argv[1]
        print(f"{xmlfile=} passed in args")
    else:
        print(f"No xml file passed, using C:\AmDesp\data\AmShip.xml")
        xmlfile = r"C:\AmDesp\data\AmShip.xml"
    shipper('prod', xmlfile)
    # programmer()
    # test()
