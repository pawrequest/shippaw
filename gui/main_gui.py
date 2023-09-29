import copy
import logging
from typing import Iterable

import PySimpleGUI as sg
from PySimpleGUI import Window
from despatchbay.despatchbay_entities import CollectionDate, Service

from core.entities import DateTimeMasks, AddressMatch
from core.funcs import collection_date_to_datetime, print_label2
from gui import keys_and_strings
from gui.gui_params import address_head_params, address_params, \
    boxes_head_params, boxes_params, date_head_params, date_params, default_params, head_params, option_menu_params, \
    shipment_params
from shipper.shipment import ShipmentQueued, ShipmentRequested, ShipmentBooked, ShipmentCompleted, ShipmentDict

logger = logging.getLogger(__name__)


def main_window(shipments: [ShipmentRequested]):
    logger.debug('BULK SHIPPER WINDOW')
    sg.set_options(**default_params)

    return sg.Window('Bulk Shipper',
                     layout=[
                         [headers()],
                         # [[self.shipment_frame(shipment=shipment)] for shipment in shipments],
                         [[shipment_frame(shipment=shipment)] for shipment in shipments],
                         [sg.Button("LETS GO", k=keys_and_strings.GO_SHIP_KEY(), expand_y=True, expand_x=True)]
                     ],
                     finalize=True)


def shipment_frame(shipment: ShipmentRequested):
    print_or_email = 'print' if shipment.is_outbound else 'email'
    date_name = keys_and_strings.DATE_STRING(collection_date=shipment.collection_date)
    recipient_address_name = keys_and_strings.ADDRESS_STRING(shipment.recipient.recipient_address)
    num_parcels = len(shipment.parcels)

    row = [
        customer_contact_button(shipment=shipment),
        sender_button(shipment=shipment),
        recipient_button(recipient_address_name=recipient_address_name, shipment=shipment),
        date_button(date_name=date_name, shipment=shipment),
        parcels_button(num_parcels=num_parcels, shipment=shipment),
        service_button(num_parcels=num_parcels, shipment=shipment),
        # sg.Checkbox('Book', default=True, k=(shipment.shipment_name, 'book')),
        sg.Checkbox('Book', default=True, k=keys_and_strings.BOOK_KEY(shipment)),
        sg.Checkbox(f'{print_or_email}', default=True, k=keys_and_strings.PRINT_EMAIL_KEY(shipment)),
        sg.Button('Drop-off', k=keys_and_strings.DROPOFF_KEY(shipment)),
        sg.Button('remove', k=keys_and_strings.REMOVE_KEY(shipment))

    ]

    layout = [row]

    return sg.Frame('', layout=layout, k=keys_and_strings.SHIPMENT_KEY(shipment), element_justification='center')


def headers():
    # but sender needs to not be a button for outbound, because it must remain defined by address id for collection to be booked
    heads = [
        # sg.Sizer(30, 0),
        sg.T('Contact / Customer', **address_head_params),
        sg.T('Sender', **address_head_params),
        sg.T('Recipient', **address_head_params),
        sg.Text('Collection Date', **date_head_params),
        sg.T('Boxes', **boxes_head_params),
        sg.T('Service', **head_params),
        sg.Push(),
        sg.Push(),
    ]

    return heads


def post_book(shipment_dict: ShipmentDict):
    headers = []
    frame = results_frame(shipment_dict=shipment_dict)
    window2 = sg.Window('Booking Results:', layout=[[frame]])
    while True:
        e2, v2 = window2.read()
        if e2 in [sg.WIN_CLOSED, 'Exit']:
            break
        if e2[1] == 'REPRINT':
            # ship_in_play = next((shipment for shipment in shipments if
            #                                         shipment.shipment_name_printable.lower() in e2.lower()))
            ship_in_play = shipment_dict[e2[0]]
            if isinstance(ship_in_play, ShipmentCompleted):
                # print_label(ship_in_play)
                print_label2(ship_in_play.label_location)
            else:
                sg.popup_quick_message('has no label')

    window2.close()


def results_frame(shipment_dict: ShipmentDict):
    params = {
        'expand_x': True,
        'expand_y': True,
        'size': (25, 2),
    }

    result_layout = []
    for shipment in shipment_dict.values():
        num_boxes = len(shipment.parcels)
        ship_res = [
            sg.Text(shipment.shipment_request.client_reference, **params),
            sg.Text(shipment.shipment_return.recipient_address.recipient_address.street, **params),
            sg.Text(keys_and_strings.SERVICE_STRING(num_boxes=num_boxes, service=shipment.service), **params),
        ]

        if shipment.is_printed:
            ship_res.extend([sg.Text('Shipment Printed', **params),
                             sg.Button('Reprint Label',
                                       key=keys_and_strings.REPRINT_KEY(shipment), **params)])
        if shipment.is_logged_to_commence:
            ship_res.append(sg.Text('Shipment ID Logged to Commence', **params))
        result_layout.append(ship_res)
    return sg.Frame('', vertical_alignment="c", layout=result_layout, element_justification='center')


def num_boxes_popup(location):
    # new_boxes = sg.popup_get_text("Enter a number")
    layout = [
        [sg.Combo(values=[i for i in range(1, 10)], enable_events=True, expand_x=True, readonly=True,
                  default_value=1,
                  k=keys_and_strings.BOX_KEY())]
    ]
    return sg.Window('', layout=layout, location=location, relative_location=(-50, -50))


def new_service_popup(menu_map: dict, location, default_service: Service) -> Service:
    layout = [
        [sg.Combo(k='-SERVICE-', values=list(menu_map.keys()), enable_events=True, default_value=default_service.name,
                  **option_menu_params)]]
    window = Window('Select a service', layout=layout, location=location, relative_location=(-100, -50))

    while True:
        event, values = window.read()
        if event == '-SERVICE-':
            window.close()
            return menu_map.get(values['-SERVICE-'])

        if event in [sg.WIN_CLOSED, "Cancel"]:
            break
        window.close()


def service_button(num_parcels, shipment):
    service_col = 'green' if shipment.default_service_matched else 'maroon4'
    service_name_button = sg.Text(f'{shipment.service.name} \n£{(num_parcels * shipment.service.cost):.2f}',
                                  background_color=service_col, enable_events=True,
                                  k=keys_and_strings.SERVICE_KEY(shipment), **shipment_params)
    return service_name_button


def parcels_button(num_parcels, shipment):
    return sg.Text(f'{num_parcels}', k=keys_and_strings.BOXES_KEY(shipment), enable_events=True, **boxes_params)


def recipient_button(recipient_address_name, shipment: ShipmentRequested):
    params = copy.deepcopy(address_params)
    if shipment.is_outbound:
        if shipment.remote_address_matched in [AddressMatch.EXPLICIT, AddressMatch.DIRECT]:
            params['background_color'] = 'green4'
        elif shipment.remote_address_matched == AddressMatch.GUI:
            params['background_color'] = 'orange4'
        else:
            logger.info("RECIPIENT COLOUR IS RED")
            params['background_color'] = 'maroon4'

    recipient_button = sg.Text(recipient_address_name, enable_events=True,
                               k=keys_and_strings.RECIPIENT_KEY(shipment), **params)
    return recipient_button


def sender_button(shipment) -> sg.Text:
    if shipment.is_outbound:
        sender_address_name = "Primary Collection Address"
        sender_button = sg.Text(sender_address_name, **address_params, background_color='green')
    else:
        if shipment.remote_address_matched in [AddressMatch.EXPLICIT, AddressMatch.DIRECT, AddressMatch.GUI]:
            colour = 'green'
        else:
            colour = 'red'
        sender_address_name = keys_and_strings.ADDRESS_STRING(address=shipment.sender.sender_address)
        sender_button = sg.Text(sender_address_name, k=keys_and_strings.SENDER_KEY(shipment), enable_events=True,
                                **address_params, background_color=colour)

    return sender_button


def customer_contact_button(shipment):
    return sg.T(f'{shipment.contact_name}\n{shipment.customer_printable}\n{shipment.address_as_str}',
                enable_events=True,
                k=keys_and_strings.CUSTOMER_KEY(shipment), **address_params)


def date_button(date_name, shipment):
    date_col = 'green' if shipment.date_matched else 'maroon4'
    collection_date_button = sg.Text(date_name, background_color=date_col, enable_events=True,
                                     k=keys_and_strings.DATE_KEY(shipment), **date_params)
    return collection_date_button


def new_date_selector(shipment: ShipmentRequested, popup_location) -> CollectionDate:
    menu_map = shipment.date_menu_map
    men_def = list(menu_map.keys())
    datetime_mask = DateTimeMasks.DISPLAY.value
    collection_date = collection_date_to_datetime(shipment.collection_date)
    default_date = f'{collection_date:{datetime_mask}}'

    layout = [
        [sg.Combo(k='-DATE-', values=men_def, enable_events=True, default_value=default_date,
                  **option_menu_params)]]

    window = Window('Select a date', layout=layout, location=popup_location, relative_location=(-100, -50))
    while True:
        event, values = window.read()
        if event in [sg.WIN_CLOSED, "Cancel"]:
            window.close()
            return shipment.collection_date
        if event == '-DATE-':
            window.close()
            return menu_map.get(values['-DATE-'])


def get_new_boxes(location) -> int | None:
    window = num_boxes_popup(location=location)
    e, v = window.read()
    if e == sg.WIN_CLOSED:
        window.close()
        return None
    if e == keys_and_strings.BOX_KEY():
        window.close()
        return int(v[e])
