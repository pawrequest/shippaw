from python.AmDespProgrammer import ProgrammingAssistant
from python.AmDespShipper import ShippingApp

def shipper(ship_mode):
    app = ShippingApp(ship_mode)
    app.prepare_shipment()
    app.process_shipment()
    return "returned from python"


def programmer():
    prog = ProgrammingAssistant()
    prog.BootUp()
    prog.ProgramBatch()
    ...


def test():
    print("SOMETHNG")


if __name__ == '__main__':
    shipper('prod')
    # programmer()
    # test()
