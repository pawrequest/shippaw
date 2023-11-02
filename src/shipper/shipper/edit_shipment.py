import logging
from enum import Enum

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Parcel
from despatchbay.despatchbay_sdk import DespatchBaySDK

from .shipment import ShipmentRequested, contact_from_shipment
from ..core.entities import Contact
from ..gui import keys_and_strings
from ..gui.address_gui import address_from_gui
from ..gui.keys_and_strings import ADDRESS_STRING, DATE_MENU, DATE_STRING, SERVICE_KEY, SERVICE_MENU, SERVICE_STRING
from ..gui.main_gui import get_new_boxes, new_date_selector, new_service_popup

logger = logging.getLogger(__name__)


def boxes_click(shipment_to_edit, window, client) -> int | None:
    new_boxes = get_new_boxes(location=window.mouse_location())
    if new_boxes is None:
        return
    shipment_to_edit.parcels = get_parcels(num_parcels=new_boxes, client=client)
    update_service_button(num_boxes=new_boxes, shipment_to_edit=shipment_to_edit, window=window)
    return new_boxes


def dropoff_click(dropoff_sender_id: str, shipment_to_edit: ShipmentRequested, client: DespatchBaySDK, window):
    if not make_shipment_dropoff(dropoff_sender_id=dropoff_sender_id, shipment_to_edit=shipment_to_edit, client=client):
        return None
    window[keys_and_strings.DROPOFF_KEY(shipment_to_edit)].update(button_color='red')
    if new_date_string := dropoff_new_date(client=client, shipment_to_edit=shipment_to_edit):
        window[keys_and_strings.DATE_KEY(shipment_to_edit)].update(new_date_string)


def make_shipment_dropoff(dropoff_sender_id, shipment_to_edit: ShipmentRequested, client: DespatchBaySDK):
    if sg.popup_yes_no('Convert To Dropoff? (y/n) (Shipment will NOT be collected!') != 'Yes':
        return None
    logger.info('Converting to Dropoff')
    shipment_to_edit.sender = client.sender(address_id=dropoff_sender_id)
    shipment_to_edit.is_dropoff = True
    return True


def dropoff_new_date(client, shipment_to_edit):
    available_dates = client.get_available_collection_dates(sender_address=shipment_to_edit.sender,
                                                            courier_id=shipment_to_edit.service.courier.courier_id)
    shipment_to_edit.date_menu_map = DATE_MENU(dates=available_dates)
    new_date = available_dates[0]
    shipment_to_edit.available_dates = available_dates

    if sg.popup_yes_no(f'Change date to {new_date.date}?') == 'Yes':
        shipment_to_edit.collection_date = new_date
        return DATE_STRING(new_date)


def date_click(shipment_to_edit, window, client=None):
    new_collection_date = new_date_selector(shipment=shipment_to_edit,
                                            popup_location=window.mouse_location())
    shipment_to_edit.collection_date = new_collection_date

    return DATE_STRING(collection_date=new_collection_date)


def customer_click(shipment_to_edit: ShipmentRequested, window=None, client=None):
    sg.popup_ok(shipment_to_edit.address_as_str)


def update_service_button(num_boxes: int, shipment_to_edit: ShipmentRequested, window):
    window[SERVICE_KEY(shipment=shipment_to_edit)].update(
        SERVICE_STRING(num_boxes=num_boxes, service=shipment_to_edit.service))


def sender_click(shipment_to_edit: ShipmentRequested, client: DespatchBaySDK, window=None):
    # contact = Contact(name=shipment_to_edit.contact_name, email=shipment_to_edit.email, telephone=shipment_to_edit.telephone)
    contact = contact_from_shipment(shipment=shipment_to_edit)
    if new_address := address_from_gui(shipment=shipment_to_edit, address=shipment_to_edit.sender.sender_address,
                                       contact=contact, client=client):
        return ADDRESS_STRING(address=new_address)


def recipient_click(shipment_to_edit: ShipmentRequested, client: DespatchBaySDK, window=None):
    contact = Contact(name=shipment_to_edit.contact_name, email=shipment_to_edit.email,
                      telephone=shipment_to_edit.telephone)
    if new_address := address_from_gui(shipment=shipment_to_edit, address=shipment_to_edit.recipient.recipient_address,
                                       contact=contact, client=client):
        return ADDRESS_STRING(address=new_address)


def service_click(shipment_to_edit: ShipmentRequested, window, client: DespatchBaySDK):
    available_services = client.get_available_services(shipment_to_edit.shipment_request)
    num_boxes = len(shipment_to_edit.parcels)
    new_service = new_service_popup(menu_map=SERVICE_MENU(available_services), location=window.mouse_location(),
                                    default_service=shipment_to_edit.service)
    if new_service is None:
        return None
    shipment_to_edit.service = new_service
    update_service_button(num_boxes=num_boxes, shipment_to_edit=shipment_to_edit, window=window)

    package = SERVICE_STRING(service=new_service, num_boxes=num_boxes)
    return package


def get_parcels(num_parcels: int, client: DespatchBaySDK, contents: str = 'Radios') -> list[Parcel]:
    """ return an array of dbay parcel objects equal to the number of boxes provided
        uses arbitrary sizes because dbay api won't allow skipping even though website does"""

    return [client.parcel(
        contents=contents,
        value=500,
        weight=6,
        length=60,
        width=40,
        height=40,
    ) for _ in range(num_parcels)]


def remove_click(shipment_to_edit: ShipmentRequested, window, client: DespatchBaySDK):
    if sg.popup_yes_no(f'Remove Shipment {shipment_to_edit.shipment_name_printable}?') == 'Yes':
        return 'REMOVE'


class ShipmentEditor(Enum):
    # spuriously tuples because then it works?
    BOXES = (boxes_click,)
    SERVICE = (service_click,)
    DATE = (date_click,)
    DROP = (dropoff_click,)
    CUSTOMER_CONTACT = (customer_click,)
    SENDER = (sender_click,)
    RECIPIENT = (recipient_click,)
    REMOVE = [remove_click]

    def __call__(self, *args, **kwargs):
        return self.value[0](*args, **kwargs)

# def get_edit_func(key):
#     return ShipmentEditor[key.upper()].value[0]
