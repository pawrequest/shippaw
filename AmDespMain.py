from python.AmDespProgrammer import ProgrammingAssistant
from python.AmDespShipper import ShippingApp


def shipper():
    app = ShippingApp()

    app.xml_to_shipment()
    if app.queue_shipment():
        app.book_collection()
    app.log_json()


def programmer():
    prog = ProgrammingAssistant()
    prog.BootUp()
    prog.ProgramBatch()
    ...


def test():
    print("SOMETHNG")


if __name__ == '__main__':
    # shipper()
    programmer()
    # test()
