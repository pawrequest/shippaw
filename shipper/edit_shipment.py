from typing import List

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Sender, Recipient, Parcel

import shipper.shipper

from core.config import logger
from core.enums import Contact
from gui import keys_and_strings
from gui.address_gui import address_from_gui
from gui.main_gui import new_date_selector, new_service_popup, new_parcels_popup
from gui.keys_and_strings import SERVICE_STRING, DATE_STRING, ADDRESS_STRING, DATE_MENU, \
    SERVICE_MENU
from shipper.addresser import sender_from_address_id
from shipper.shipment import Shipment


def boxes_click(shipment_to_edit, window):
    new_parcels = get_new_parcels(location=window.mouse_location())
    if new_parcels is None:
        return None
    shipment_to_edit.parcels = new_parcels
    update_service(new_parcels, shipment_to_edit, window)
    return len(shipment_to_edit.parcels)

    # update_parcels(new_parcels, shipment_to_edit, window)


def dropoff_click(config, shipment: Shipment):
    client = shipper.shipper.DESP_CLIENT

    if sg.popup_yes_no('Convert To Dropoff? (y/n) (Shipment will NOT be collected!') != 'Yes':
        return None
    logger.info('Converting to Dropoff')
    shipment.sender = sender_from_address_id(address_id=config.home_address.dropoff_sender_id)
    available_dates = client.get_available_collection_dates(sender_address=shipment.sender,
                                                                 courier_id=config.default_shipping_service.courier)
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


def update_service(new_parcels, shipment_to_edit, window):
    window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
        f'{shipment_to_edit.service.name} \n£{len(new_parcels) * shipment_to_edit.service.cost:.2f}')


def update_service_el(new_parcels, shipment_to_edit, service_button):
    service_button.update(
        f'{shipment_to_edit.service.name} \n£{len(new_parcels) * shipment_to_edit.service.cost:.2f}')


def address_click(target: Sender | Recipient, shipment: Shipment):
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


def service_click(shipment_to_edit, location):
    new_service = new_service_popup(default_service=shipment_to_edit.service.name,
                                    menu_map=SERVICE_MENU(
                                           shipment_to_edit.available_services),
                                    location=location)
    if new_service is None:
        return None
    shipment_to_edit.service = new_service
    return SERVICE_STRING(service=new_service, num_boxes=len(shipment_to_edit.parcels))


def get_new_parcels(location, parcel_contents="Radios") -> List[Parcel] | None:
    window = new_parcels_popup(location=location)
    e, v = window.read()
    if e == sg.WIN_CLOSED:
        window.close()
        return None
    if e == keys_and_strings.BOX_KEY():
        new_boxes = int(v[e])
        window.close()
        return get_parcels(num_parcels=new_boxes, contents=parcel_contents)


def get_parcels(num_parcels: int, contents: str = 'Radios') -> list[Parcel]:
    """ return an array of dbay parcel objects equal to the number of boxes provided
        uses arbitrary sizes because dbay api wont allow skipping even though website does"""
    client = shipper.shipper.DESP_CLIENT
    # parcels = []
    # for x in range(num_parcels):
    #     parcel = client.parcel(
    #         contents=contents,
    #         value=500,
    #         weight=6,
    #         length=60,
    #         width=40,
    #         height=40,
    #     )
    #     parcels.append(parcel)
    # return parcels
    # logger.info(f'PREPPING SHIPMENT - {len(parcels)} PARCELS ')

    return [client.parcel(
                contents=contents,
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )for i in range(num_parcels)]

