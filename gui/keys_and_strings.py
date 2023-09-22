from datetime import datetime
from typing import List

from despatchbay.despatchbay_entities import Address, CollectionDate, Service

from core.entities import DateTimeMasks
from shipper.shipment import ShipmentRequested



def BOOK_KEY(shipment: ShipmentRequested):
    return shipment.shipment_name, 'BOOK'

def BOXES_KEY(shipment):
    return shipment.shipment_name, 'BOXES'


def BOX_KEY():
    return '-BOX-'


def CUSTOMER_KEY(shipment):
    return shipment.shipment_name, 'CUSTOMER_CONTACT'


def DATE_KEY(shipment):
    return shipment.shipment_name, 'DATE'


def DROPOFF_KEY(shipment):
    return shipment.shipment_name, 'DROP'


def GO_SHIP_KEY():
    return '-GO_SHIP-'


def PRINT_EMAIL_KEY(shipment: ShipmentRequested):
    return shipment.shipment_name, 'PRINT_EMAIL'


def RECIPIENT_KEY(shipment):
    return shipment.shipment_name, 'RECIPIENT'


def REMOVE_KEY(shipment: ShipmentRequested):
    return shipment.shipment_name, 'REMOVE'


def REPRINT_KEY(shipment):
    return shipment.shipment_name, 'REPRINT'


def SHIPMENT_KEY(shipment: ShipmentRequested):
    return shipment.shipment_name, 'SHIPMENT'


def SENDER_KEY(shipment):
    return shipment.shipment_name, 'SENDER'


def SERVICE_KEY(shipment):
    return shipment.shipment_name, 'SERVICE'



def SERVICE_STRING(num_boxes: int, service: Service):
    return f'{service.name}\n{num_boxes * service.cost:.2f}'


def DATE_STRING(collection_date: CollectionDate):
    return f'{datetime.strptime(collection_date.date, DateTimeMasks.DB.value):{DateTimeMasks.BUTTON.value}}'


def ADDRESS_STRING(address: Address):
    return f'{address.company_name if address.company_name else "< no company name >"}\n{address.street}\n{address.locality if address.locality else ""}\n{address.town_city}'


def DATE_MENU(dates: list[CollectionDate]):
    menu_map = {}
    for potential_collection_date in dates:
        real_date = datetime.strptime(potential_collection_date.date, DateTimeMasks.DB.value).date()
        display_date = real_date.strftime(DateTimeMasks.DISPLAY.value)
        menu_map.update({display_date: potential_collection_date})
    return menu_map


def SERVICE_MENU(available_services: List[Service]):
    """returns a dict of service names to service objects"""
    return {service.name: service for service in available_services}




def collection_booked_string(shipment):
    return f"Collection Booked for {shipment.collection_date_datetime:{DateTimeMasks.DISPLAY.value}} -" if shipment.is_booked else ""

def label_filename_outbound(shipment):
    return f'{shipment.customer_printable} - Shipping Label - {collection_booked_string(shipment)} booked at {shipment.timestamp}'

def label_filename_inbound(shipment):
    return f'{shipment.customer_printable} - Returns Label - {collection_booked_string(shipment)} booked at {shipment.timestamp}'
