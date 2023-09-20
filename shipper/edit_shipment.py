import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Parcel, Recipient, Sender, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK

from core.config import logger
from core.enums import Contact
from gui import keys_and_strings
from gui.address_gui import address_from_gui
from gui.keys_and_strings import ADDRESS_STRING, DATE_MENU, DATE_STRING, SERVICE_KEY, SERVICE_MENU, SERVICE_STRING
from gui.main_gui import new_date_selector, new_service_popup, num_boxes_popup
from shipper.shipment import ShipmentRequested


def boxes_click(shipment_to_edit, window, client) -> int | None:
    new_boxes = get_new_boxes(location=window.mouse_location())
    if new_boxes is None:
        return
    shipment_to_edit.parcels = get_parcels(num_parcels=new_boxes, client=client)
    update_service_button(num_boxes=new_boxes, shipment_to_edit=shipment_to_edit, window=window)
    return new_boxes



def dropoff_click(config, shipment: ShipmentRequested, client: DespatchBaySDK):
    if sg.popup_yes_no('Convert To Dropoff? (y/n) (Shipment will NOT be collected!') != 'Yes':
        return None
    logger.info('Converting to Dropoff')
    # shipment.sender = sender_from_address_id(address_id=config.home_address.dropoff_sender_id)
    shipment.sender = client.sender(address_id=config.home_address.dropoff_sender_id)

    shipment.is_dropoff = True
    available_dates = client.get_available_collection_dates(sender_address=shipment.sender,
                                                            courier_id=config.default_courier.courier)
    shipment.date_menu_map = DATE_MENU(dates=available_dates)
    new_date = available_dates[0]
    shipment.available_dates = available_dates
    if sg.popup_yes_no(f'Change date to {new_date.date}?') == 'Yes':
        shipment.collection_date = new_date
        return DATE_STRING(new_date)


def date_click(location, shipment_to_edit):
    new_collection_date = new_date_selector(shipment=shipment_to_edit,
                                            popup_location=location)
    shipment_to_edit.collection_date = new_collection_date

    return DATE_STRING(collection_date=new_collection_date)


def update_service_button(num_boxes: int, shipment_to_edit: ShipmentRequested, window):
    window[SERVICE_KEY(shipment=shipment_to_edit)].update(
        SERVICE_STRING(num_boxes=num_boxes, service=shipment_to_edit.service))


def address_click(target: Sender | Recipient, shipment: ShipmentRequested):
    """ Takes a Sender or Recipient and returns a new address for that sender or recipient or None if exit """
    contact = Contact(name=target.name, email=target.email, telephone=target.telephone)
    if isinstance(target, Sender):
        address_to_edit = shipment.sender.sender_address
    elif isinstance(target, Recipient):
        address_to_edit = shipment.recipient.recipient_address
    else:
        raise TypeError(f'add_click target must be Sender or Recipient, not {type(target)}')

    new_address = address_from_gui(shipment=shipment, address=address_to_edit,
                                   contact=contact)
    if new_address is None:
        return None

    address_to_edit = new_address
    return ADDRESS_STRING(address=address_to_edit)


def service_click(shipment_to_edit: ShipmentRequested, location, default_service: Service, client: DespatchBaySDK):
    available_services = client.get_available_services(shipment_to_edit.shipment_request)
    new_service = new_service_popup(menu_map=SERVICE_MENU(available_services), location=location,
                                    default_service=default_service)
    if new_service is None:
        return None
    shipment_to_edit.service = new_service
    package = SERVICE_STRING(service=new_service, num_boxes=len(shipment_to_edit.parcels))
    return package


def get_new_boxes(location) -> int | None:
    window = num_boxes_popup(location=location)
    e, v = window.read()
    if e == sg.WIN_CLOSED:
        window.close()
        return None
    if e == keys_and_strings.BOX_KEY():
        window.close()
        return int(v[e])


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
