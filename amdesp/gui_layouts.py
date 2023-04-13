from collections import namedtuple
from typing import Literal

import PySimpleGUI as sg
from PySimpleGUI import Window
from dateutil.parser import parse
from amdesp.despatchbay.despatchbay_entities import Address, Recipient, Sender, AddressKey
from amdesp.config import Config
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.shipment import Shipment

BestMatch = namedtuple('BestMatch', ['str_matched', 'address', 'category', 'score'])

default_params = {
    'font': 'Rockwell 14',
    'element_padding': (25, 5),
    'border_width': 3,
}

bulk_params = {
    'size': (15, 2),
    'justification': 'center',
    'pad': (5, 5),
    'border_width': 4,
    'relief': sg.RELIEF_GROOVE,
    'auto_size_text': True,
}

head_params = {
    'size': (15, 2),
    'justification': 'center',
    'pad': (5, 5),
    'auto_size_text': True,
}

recip_params = {
    'size': (45, 2),
    'justification': 'center',
    'pad': (5, 5),
    'border_width': 4,
    'relief': sg.RELIEF_GROOVE,
    'auto_size_text': True,
}

recip_head_params = {
    'size': (45, 2),
    'justification': 'center',
    'pad': (5, 5),
    'auto_size_text': True,
}

boxes_head_params = {
    'size': (5, 2),
    'justification': 'center',
    'pad': (5, 5),
    'auto_size_text': True,
}

boxes_params = {
    'size': (5, 2),
    'justification': 'center',
    'pad': (5, 5),
    'border_width': 4,
    'relief': sg.RELIEF_GROOVE,
    'auto_size_text': True,
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


def booked_shipments_frame(shipments: [Shipment]):
    params = {
        'expand_x': True,
        'expand_y': True,
        'size': (25, 2)
    }

    result_layout = []
    for shipment in shipments:
        ship_res = []
        ship_res.append(sg.Text(shipment.shipment_request.client_reference, **params))
        ship_res.append(sg.Text(shipment.shipment_return.recipient_address.recipient_address.street, **params))
        ship_res.append(sg.Text(f'{shipment.service.name} - {len(shipment.parcels)} boxes = £{shipment.service.cost}'))
        if shipment.printed:
            ship_res.append(sg.Text('Shipment Printed'))
        if shipment.logged_to_commence:
            ship_res.append(sg.Text('Shipment ID Logged to Commence'))
        # result_layout.append([sg.Frame('', layout=[ship_res])])
        result_layout.append(ship_res)
        # result_layout.append([sg.Text('')])
    return sg.Frame('', layout=result_layout)


def bulk_shipper_window(shipments: [Shipment], config: Config):
    if config.sandbox:
        sg.theme('Tan')
    else:
        sg.theme('Dark Blue')

    sg.set_options(**default_params)
    layout = []
    headers = [
        sg.Push(),
        sg.T('Customer', **head_params),
        sg.Text('Collection Date', **head_params),
        sg.T('Sender', **head_params),
        sg.T('Recipient', **recip_head_params),
        sg.T('Boxes', **boxes_head_params),
        sg.T('Service', **head_params)
    ]
    layout.append(headers)

    for shipment in shipments:
        collection_date = parse(shipment.collection_date.date).date()
        date_col = 'green' if shipment.send_out_date == collection_date else 'maroon4'
        service_col = 'green' if shipment.default_service_matched else 'maroon4'
        address_name = get_address_button_string(shipment.recipient.recipient_address)
        friendly_date = f'{parse(shipment.collection_date.date):{config.datetime_masks["DT_DISPLAY"]}}'
        num_parcels = len(shipment.parcels)

        layout.append(
            # remove button
            [sg.Button('remove', k=f'-{shipment.shipment_name}_REMOVE-'),
             sg.T(shipment.customer, **bulk_params),

             # shipment name
             sg.Text(friendly_date, background_color=date_col, enable_events=True,
                     k=f'-{shipment.shipment_name.upper()}_DATE-', **bulk_params),

             # Sender
             sg.T(shipment.sender.sender_address.street, enable_events=True,
                  k=f'-{shipment.shipment_name.upper()}_SENDER-', **bulk_params),

             # Recipient
             sg.Text(address_name, enable_events=True,
                     k=f'-{shipment.shipment_name.upper()}_RECIPIENT-', **recip_params),
             # Boxes
             sg.Text(f'{num_parcels}', k=f'-{shipment.shipment_name.upper()}_BOXES-', enable_events=True,
                     **boxes_params),
             # Service
             sg.Text(f'{shipment.service.name} \n£{num_parcels * shipment.service.cost}',
                     background_color=service_col,
                     enable_events=True, k=f'-{shipment.shipment_name.upper()}_SERVICE-', **bulk_params)]
        )

    layout.append([
        [sg.Button("LETS GO", k='-GO_SHIP-', expand_y=True, expand_x=True)]
    ])
    window = sg.Window('Bulk Shipper', layout=layout, finalize=True)
    return window


def get_c(address: Address):
    return f'{address.company_name} \n {address.street}' if address.company_name else address.street


def get_address_button_string(address):
    return f'{address.company_name}\n{address.street}' if address.company_name else address.street


def remote_address_frame(shipment: Shipment, config: Config, address: Address):
    # sender_or_recip = shipment.get_sender_or_recip()
    # key_string = type(sender_or_recip).__name__.upper()

    layout = [
        [sg.Text(f'Name:', **address_fieldname_params),
         sg.InputText(f'{shipment.contact}', key=f'-NAME-', **address_input_params)],

        [sg.Text(f'Email:', **address_fieldname_params),
         sg.InputText(f'{shipment.email}', key=f'-EMAIL-', **address_input_params)],

        [sg.Text(f'Telephone:', **address_fieldname_params),
         sg.InputText(f'{shipment.telephone}', key=f'-TELEPHONE-', **address_input_params)],

        [get_address_frame(address=address, config=config)],

        [sg.B('Submit', k=f'-SUBMIT-')]
    ]

    # noinspection PyTypeChecker
    frame = sg.Frame(f'Remote Address', layout=layout, k=f'-REMOTE_ADDRESS-', pad=20, font="Rockwell 30",
                     border_width=5, relief=sg.RELIEF_GROOVE,
                     title_location=sg.TITLE_LOCATION_TOP)
    return frame


def new_date_selector(shipment: Shipment, config: Config):
    menu_map = shipment.date_menu_map
    men_def = [k for k in menu_map.keys()]
    datetime_mask = config.datetime_masks['DT_DISPLAY']
    default_date = f'{parse(shipment.collection_date.date).date():{datetime_mask}}'

    layout = [
        [sg.Combo(k='-DATE-', values=men_def, enable_events=True, default_value=default_date, **option_menu_params)]]

    window = Window('Select a date', layout=layout)
    while True:
        e, v = window.read()
        if e in [sg.WIN_CLOSED, "Cancel"]:
            window.close()
            return shipment.collection_date
        if 'date' in e.lower():
            window.close()
            return menu_map.get(v['-DATE-'])


def new_service_selector(shipment: Shipment):
    menu_map = shipment.service_menu_map
    men_def = [k for k in menu_map.keys()]

    layout = [[sg.Combo(k='-SERVICE-', values=men_def, enable_events=True, default_value=shipment.service.name,
                        **option_menu_params)]]
    window = Window('Select a service', layout=layout)

    while True:
        e, v = window.read()
        if e in [sg.WIN_CLOSED, "Cancel"]:
            window.close()
            return shipment.service
        if 'service' in e.lower():
            window.close()
            return menu_map.get(v['-SERVICE-'])


def get_service_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
    """ gets available shipping services for shipment sender and recipient
    builds menu_def of potential services and if any matches service_id specified in config.toml then select it by default
     return a dict of menu_def and default_value"""
    services = client.get_services()
    # todo get AVAILABLE services needs a request
    # services = client.get_available_services()
    shipment.service_menu_map.update({service.name: service for service in services})
    chosen_service = next((service for service in services if service.service_id == config.dbay['service_id']),
                          services[0])
    shipment.service = chosen_service
    return {'values': [service.name for service in services], 'default_value': chosen_service.name}


def get_address_frame(config: Config, address: Address, index: str = None) -> sg.Frame:
    layout = []
    params = address_fieldname_params.copy()
    address_fields = config.address_fields
    input_text = ''
    for field in address_fields:
        if index:
            upper_key = f'-ADDRESS_{field}-'.upper()
            lower_key = f'-ADDRESS_{field}-'.lower()
        else:
            upper_key = f'-ADDRESS_{field}-'.upper()
            lower_key = f'-ADDRESS_{field}-'.lower()
        if isinstance(address, Address):
            input_text = getattr(address, field)
        key_for_humans = field.title().replace('_', ' ')

        if field in ('company_name', 'postal_code'):
            # is a button
            params.pop('justification', None)
            label_text = sg.B(key_for_humans, k=lower_key, **params)
        else:
            label_text = sg.Text(key_for_humans, k=lower_key, **address_fieldname_params)

        input_box = sg.InputText(input_text, k=upper_key, **address_input_params)
        layout.append([label_text, input_box])

    frame = sg.Frame('Address', layout, pad=20, )
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


def compare_addresses_window(address: Address, address_dict: dict, config: Config):
    layout = [[get_address_frame(config=config, address=address),
               get_address_dict_frame(address_dict=address_dict, config=config)],
              [sg.Submit(k='-COMPARE_SUBMIT-')]
              ]

    frame = sg.Frame(f'Compare Addresses', layout=layout, k=f'-COMPARE_ADDRESS-', pad=20, font="Rockwell 30",
                     border_width=5, relief=sg.RELIEF_GROOVE, title_location=sg.TITLE_LOCATION_TOP)

    window = sg.Window('Compare Addresses', layout=[[frame]])

    return window


def get_address_dict_frame(config: Config, address_dict):
    layout = []
    params = address_fieldname_params.copy()
    address_fields = config.address_fields
    for field in address_fields:
        upper_key = f'-ADDRESS_DICT_{field}-'.upper()
        lower_key = f'-ADDRESS_DICT_{field}-'.lower()
        address_field = field.title().replace('_', ' ')
        address_value = address_dict.get(field)

        # if field in ('company_name', 'postal_code'):
        #     # is a button
        #     params.pop('justification', None)
        #     label_text = sg.B(key_for_humans, k=lower_key, **params)
        # else:
        label_text = sg.Text(address_field, k=lower_key, **address_fieldname_params)

        input_box = sg.InputText(address_value, k=upper_key, **address_input_params)
        layout.append([label_text, input_box])

    frame = sg.Frame('Address', layout, pad=20, )
    return frame


def shipment_name_element() -> sg.Text:
    element = sg.Text('', expand_x=True, expand_y=True, justification='center',
                      font='Rockwell 30',
                      border_width=8, relief=sg.RELIEF_GROOVE, k='-SHIPMENT_NAME-')
    return element


def address_chooser_popup(candidate_dict: dict, client: DespatchBaySDK) -> Address:
    """ popup mapping address keys to human readable addresses
    :param address_dict - a dicitonary of addresses (keys) and their dbay keys (values)
    :return dbay address key
    """
    default_value = next(c for c in candidate_dict)

    layout = [
        [sg.Listbox(list(candidate_dict.keys()), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, expand_x=True,
                    expand_y=True, enable_events=True, size=(50, 20), bind_return_key=True,
                    default_values=default_value, k='select')],
    ]

    window = sg.Window('Address Selector', layout)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'select':
            address_key = candidate_dict.get(values['select'][0])
            address = client.get_address_by_key(address_key)
            window.close()
            return address
        else:
            continue
