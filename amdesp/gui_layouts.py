from typing import Literal

import PySimpleGUI as sg
from PySimpleGUI import Window

from amdesp.despatchbay.despatchbay_entities import Address
from amdesp.config import Config
address_fields = Config.get_config_from_toml()['address_fields']

default_params = {
    'font': 'Rockwell 14',
    'element_padding': (25, 5),
    'border_width': 3,
}

address_input_params = {
    'size': (18, 1),
    'justification': 'left',
    'expand_x': True,
    'pad': (20, 8),
}

address_fieldname_params = {
    'size': (15, 1),
    'justification': 'center',
    'pad': (20, 8),
}

option_menu_params = {
    'pad': (10, 5),
    'size': (30, 1),
    'readonly': True,
}

def main_window()-> Window:
    sg.set_options(**default_params)
    # elements
    shipment_name = shipment_name_element()
    sender = sender_receiver_frame('sender')
    recipient = sender_receiver_frame('recipient')
    # todo get addresses before dates
    date_match = date_chooser()
    parcels = parcels_spin()
    service = service_combo()
    queue = queue_or_book_combo()
    ids = shipment_ids_frame()
    book_button = go_button()

    # frames
    button_layout = [
        [date_match],
        [parcels],
        [service],
        [queue],
    ]
    button_col = sg.Column(layout=button_layout, element_justification='center', pad=20, expand_x=True)
    button_frame = sg.Frame('', layout=[[button_col, book_button]], pad=20, element_justification='center',
                            border_width=8,
                            relief=sg.RELIEF_GROOVE)
    layout = [[shipment_name],
              [sender, recipient],
              [ids, sg.P(), button_frame]
              ]
    window = sg.Window("Paul Sees Solutions - AmDesp Shipping Client", layout, finalize=True)
    return window



def sender_receiver_frame(mode):
    title = mode.title()
    layout = [
        [sg.Text(f'Name:', **address_fieldname_params),
         sg.InputText(key=f'-{title.upper()}_NAME-', **address_input_params)],

        [sg.Text(f'Email:', **address_fieldname_params),
         sg.InputText(key=f'-{title.upper()}_EMAIL-', **address_input_params)],

        [sg.Text(f'Telephone:', **address_fieldname_params),
         sg.InputText(key=f'-{title.upper()}_TELEPHONE-', **address_input_params)],

        [address_frame(sender_or_recipient=mode)],
    ]

    k = f'-{title.upper()}-'
    # noinspection PyTypeChecker
    frame = sg.Frame(f'{title}', layout, k=k, pad=20, font="Rockwell 30", border_width=5, relief=sg.RELIEF_GROOVE,
                     title_location=sg.TITLE_LOCATION_TOP)
    return frame


def service_combo():
    return sg.Combo(k='-SERVICE-', values=[], **option_menu_params)


def queue_or_book_combo():
    return sg.Combo(values=[], k='-QUEUE_OR_BOOK-', **option_menu_params)


def address_frame(sender_or_recipient: Literal['sender', 'recipient']) -> sg.Frame:
    layout = []
    params = address_fieldname_params.copy()

    for attr in address_fields:
        key = f'-{sender_or_recipient}_{attr}-'.upper()
        key_hr = attr.title().replace('_', ' ')

        if attr in ('company_name', 'postal_code'):
            # is a button
            params.pop('justification', None)
            label_text = sg.B(key_hr, k=key.lower(), **params)
        else:
            label_text = sg.Text(key_hr, k=key.lower(), **address_fieldname_params)

        input_box = sg.InputText(k=key, **address_input_params)
        layout.append([label_text, input_box])

    frame = sg.Frame(f"{sender_or_recipient.title()} Address", layout, k=f'-{sender_or_recipient.upper()}_ADDRESS-',
                     pad=20, )
    return frame


def parcels_spin() -> sg.Combo:
    element = sg.Combo(k='-BOXES-', values=[i for i in range(10)], **option_menu_params)

    return element


def shipment_ids_frame() -> sg.Frame:
    layout = []
    for direction in ['inbound', 'outbound']:
        layout.append(
            [sg.T('', font='Rockwell 20', size=20, border_width=3, justification='center', relief=sg.RELIEF_GROOVE,
                  pad=20, k=f'-{direction.upper()}_ID-')])

    frame = sg.Frame('Shipment IDs', layout, pad=20, element_justification='center',
                     border_width=8,
                     relief=sg.RELIEF_GROOVE, expand_y=True)
    return frame


# todo
def tracking_viewer_window(shipment_id, client):
    try:
        shipment = client.get_shipment(shipment_id)
        tracking_numbers = [parcel.tracking_number for parcel in shipment.parcels]
        tracking_d = {}
        sublayout = []
        parcel_frame = None
        signatory = None
        params = {}
        for tracked_parcel in tracking_numbers:
            tracking = client.get_tracking(tracked_parcel)
            # courier = tracking['CourierName'] # debug unused?
            # parcel_title = [f'{tracked_parcel} ({courier}):'] # debug unused?
            history = tracking['TrackingHistory']
            for event in history:
                if 'delivered' in event.Description.lower():
                    signatory = f"{chr(10)}Signed for by: {event.Signatory}"
                    params.update({'background_color': 'aquamarine', 'text_color': 'red'})

                event_text = sg.T(
                    f'{event.Date} - {event.Description} in {event.Location}{signatory if signatory else ""}',
                    **params)
                sublayout.append([event_text])

            parcel_frame = [sg.Column(sublayout)]
            tracking_d.update({tracked_parcel: tracking})

    except Exception as e:
        sg.popup_error(e)
    else:
        shipment.tracking_dict = tracking_d
        tracking_window = sg.Window('', [parcel_frame])
        tracking_window.read()


def shipment_name_element() -> sg.Text:
    element = sg.Text('', expand_x=True, expand_y=True, justification='center',
                      font='Rockwell 30',
                      border_width=8, relief=sg.RELIEF_GROOVE, k='-SHIPMENT_NAME-')
    return element


def address_chooser_popup(address_dict: dict) -> Address:
    """ popup mapping address keys to human readable addresses
    :param address_dict - a dicitonary of addresses (keys) and their dbay keys (values)
    :return dbay address key
    """

    default_value = list(address_dict.keys())[0]
    layout = [
        [sg.Combo(list(address_dict.keys()), default_value=default_value, enable_events=True, readonly=True,
                  k='select')],
    ]

    window = sg.Window('Address Selector', layout)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'select':
            if values:
                selected_option = values['select']
                window.close()
                return address_dict.get(selected_option)
        continue


def date_chooser() -> sg.Combo:
    return sg.Combo(values=[], pad=(10, 5), size=30, readonly=True, k='-DATE-')


def go_button():
    return sg.Button(f'Go!', k="-GO-", size=(12, 5), expand_y=True, pad=20, )
