from shipper.shipment import Shipment


def GO_SHIP():
    return '-GO_SHIP-'


def REMOVE(shipment: Shipment):
    return f'-{shipment.shipment_name_printable}_REMOVE-'.upper()


def BOOK(shipment: Shipment):
    return f'-{shipment.shipment_name_printable}_BOOK-'.upper()


def PRINT_EMAIL(shipment: Shipment):
    return f'-{shipment.shipment_name_printable}_PRINT_EMAIL-'.upper()


def SHIPMENT(shipment: Shipment):
    return f'-SHIPMENT_{shipment.shipment_name_printable}-'.upper()


def BOX():
    return '-BOX-'


def SERVICE(shipment):
    return f'-{shipment.shipment_name_printable.upper()}_SERVICE-'.upper()


def BOXES(shipment):
    return f'-{shipment.shipment_name_printable.upper()}_BOXES-'.upper()


def RECIPIENT(shipment):
    return f'-{shipment.shipment_name_printable.upper()}_RECIPIENT-'.upper()


def SENDER(shipment):
    return f'-{shipment.shipment_name_printable}_SENDER-'.upper()


def CUSTOMER_CONTACT(shipment):
    return f"-{shipment.shipment_name_printable}_CUSTOMER_CONTACT-".upper()


def DATE(shipment):
    return f'-{shipment.shipment_name_printable.upper()}_DATE-'.upper()


def REPRINT(shipment):
    return f'-{shipment.shipment_name_printable.upper()}_REPRINT-'.upper()


def DROPOFF(shipment):
    return f'-{shipment.shipment_name_printable}_DROP-'.upper()
