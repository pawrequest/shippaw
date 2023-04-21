from datetime import datetime

import PySimpleGUI as sg
from PySimpleGUI import Window
from dateutil.parser import parse
from amdesp.despatchbay.despatchbay_entities import Address, CollectionDate
from amdesp.config import Config, get_amdesp_logger, Contact
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.gui_params import default_params, address_head_params, head_params, date_head_params, boxes_head_params, \
    shipment_params, address_fieldname_params, address_input_params, option_menu_params, boxes_params, address_params, \
    date_params
from amdesp.shipment import Shipment

logger = get_amdesp_logger()


def bulk_shipper_window(shipments: [Shipment], config: Config):
    logger.info('BULK SHIPPER WINDOW')
    if config.sandbox:
        sg.theme('Tan')
    else:
        sg.theme('Dark Blue')

    print_or_email = 'print' if config.outbound else 'email'

    sg.set_options(**default_params)
    layout = []
    headers = [
        # sg.Sizer(30, 0),
        sg.T('Contact / Customer', **head_params),
        sg.T('Sender', **address_head_params),
        sg.T('Recipient', **address_head_params),
        sg.Text('Collection Date', **date_head_params),
        sg.T('Boxes', **boxes_head_params),
        sg.T('Service', **head_params),
        # sg.T('Add Shipment', **head_params),
        # sg.T('Book Collection', **head_params),
        # sg.T(print_or_email.title(), **head_params),
        sg.Push(),
        sg.Push(),
    ]
    layout.append(headers)

    for shipment in shipments:
        date_name = get_date_label(config=config, collection_date=shipment.collection_date)
        collection_date = datetime.strptime(shipment.collection_date.date, config.datetime_masks['DT_DB']).date()

        date_col = 'green' if shipment.send_out_date == collection_date else 'maroon4'
        service_col = 'green' if shipment.default_service_matched else 'maroon4'

        sender_address_name = get_address_button_string(shipment.sender.sender_address)
        recipient_address_name = get_address_button_string(shipment.recipient.recipient_address)

        num_parcels = len(shipment.parcels)

        remove_button = sg.Button('remove', k=f'-{shipment.shipment_name_printable}_REMOVE-')
        customer_display = sg.T(f'{shipment.contact_name}\n{shipment.customer}', **shipment_params)
        collection_date_button = get_date_button(date_col, date_name, shipment)
        sender_button = get_sender_button(sender_address_name, shipment)
        recipient_button = get_recip_button(recipient_address_name, shipment)
        parcels_button = get_parcels_button(num_parcels, shipment)
        service_name_button = get_service_button(num_parcels, service_col, shipment)


        frame_lay = [[
            customer_display,
            sender_button,
            recipient_button,
            collection_date_button,
            parcels_button,
            service_name_button,
            sg.Checkbox('Add', default=True),
            sg.Checkbox('Book', default=True),
            sg.Checkbox(f'{print_or_email}', default=True, ),
            remove_button
        ]]
        frame = sg.Frame('', layout=frame_lay, k=f'-SHIPMENT_{shipment.shipment_name_printable}-'.upper())

        layout.append([frame])

    layout.append([
        [sg.Button("LETS GO", k='-GO_SHIP-', expand_y=True, expand_x=True)]
    ])
    window = sg.Window('Bulk Shipper', layout=layout, finalize=True)
    return window


def booked_shipments_frame(shipments: [Shipment]):
    params = {
        'expand_x': True,
        'expand_y': True,
        'size': (25, 2)
    }

    result_layout = []
    for shipment in shipments:
        ship_res = [sg.Text(shipment.shipment_request.client_reference, **params),
                    sg.Text(shipment.shipment_return.recipient_address.recipient_address.street, **params),
                    sg.Text(f'{shipment.service.name} - {len(shipment.parcels)} boxes = £{shipment.service.cost}')]

        if shipment.printed:
            ship_res.append(sg.Text('Shipment Printed'))
        if shipment.logged_to_commence:
            ship_res.append(sg.Text('Shipment ID Logged to Commence'))
        # result_layout.append([sg.Frame('', layout=[ship_res])])
        result_layout.append(ship_res)
        # result_layout.append([sg.Text('')])
    return sg.Frame('', layout=result_layout)


def get_address_frame(config: Config, address: Address, index: str = None) -> sg.Frame:
    layout = []
    params = address_fieldname_params.copy()
    address_fields = config.fields.address
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

    frame = sg.Frame('Address', layout, pad=20)
    return frame


def get_address_button_string(address):
    # return f'{address.company_name}\n{address.street}' if address.company_name else address.street
    return f'{address.company_name if address.company_name else "< no company name >"}\n{address.street}'


def new_date_selector(shipment: Shipment, config: Config, location):
    location = location
    menu_map = shipment.date_menu_map
    men_def = [k for k in menu_map.keys()]
    datetime_mask = config.datetime_masks['DT_DISPLAY']
    default_date = f'{parse(shipment.collection_date.date).date():{datetime_mask}}'

    layout = [
        [sg.Combo(k='-DATE-', values=men_def, enable_events=True, default_value=default_date,
                  **option_menu_params)]]

    window = Window('Select a date', layout=layout, location=location, relative_location=(-100, -50))
    while True:
        e, v = window.read()
        if e in [sg.WIN_CLOSED, "Cancel"]:
            window.close()
            return shipment.collection_date
        if 'date' in e.lower():
            window.close()
            return menu_map.get(v['-DATE-'])


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


def tracking_viewer_window(shipment_id, client):
    logger.info(f'TRACKING VIEWER GUI - SHIPMENT ID: {shipment_id}')
    shipment_return = client.get_shipment(shipment_id)
    tracking_numbers = [parcel.tracking_number for parcel in shipment_return.parcels]
    tracking_d = {}
    layout = []
    for tracked_parcel in tracking_numbers:
        parcel_layout = []
        parcel_col = None
        signatory = None
        params = {}
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

            parcel_layout.append([event_text])

        parcel_col = sg.Column(parcel_layout)
        layout.append(parcel_col)
        tracking_d.update({tracked_parcel: tracking})

    shipment_return.tracking_dict = tracking_d
    tracking_window = sg.Window('', [layout])
    tracking_window.read()


def get_address_dict_frame(config: Config, address_dict):
    layout = []
    address_fields = config.fields.address
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


def shipment_name_printable_element() -> sg.Text:
    element = sg.Text('', expand_x=True, expand_y=True, justification='center',
                      font='Rockwell 30',
                      border_width=8, relief=sg.RELIEF_GROOVE, k='-shipment_name_printable-')
    return element


def address_chooser_popup(candidate_dict: dict, client: DespatchBaySDK) -> Address:
    """ popup mapping address keys to human readable addresses
    """
    default_value = next(c for c in candidate_dict)

    layout = [[sg.Listbox(list(candidate_dict.keys()), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, expand_x=True,
                          expand_y=True, enable_events=True, size=(50, 20), bind_return_key=True,
                          default_values=default_value, k='select', auto_size_text=True)]]

    # layout = [
    #     [sg.Combo(values = list(candidate_dict.keys()),default_value=default_value,
    #               size=(50, 20),
    #               expand_x=True, expand_y=True,
    #               enable_events=True, readonly=True, bind_return_key=True,
    #               k='select',
    #               auto_size_text=True)],
    # ]

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


def loading():
    layout = [
        [sg.Text("Loading Shipments")]
    ]

    return sg.Window('Loading', layout, modal=True, disable_close=True, finalize=True)


def compare_addresses_window(address: Address, address_dict: dict, config: Config):
    layout = [[get_address_frame(config=config, address=address),
               get_address_dict_frame(address_dict=address_dict, config=config)],
              [sg.Submit(k='-COMPARE_SUBMIT-')]
              ]

    frame = sg.Frame(f'Compare Addresses', layout=layout, k=f'-COMPARE_ADDRESS-', pad=20, font="Rockwell 30",
                     border_width=5, relief=sg.RELIEF_GROOVE, title_location=sg.TITLE_LOCATION_TOP)

    window = sg.Window('Compare Addresses', layout=[[frame]])

    return window


def new_service_selector(shipment: Shipment, location):
    menu_map = shipment.service_menu_map
    men_def = [k for k in menu_map.keys()]

    layout = [[sg.Combo(k='-SERVICE-', values=men_def, enable_events=True, default_value=shipment.service.name,
                        **option_menu_params)]]
    window = Window('Select a service', layout=layout, location=location, relative_location=(-100, -50))

    while True:
        e, v = window.read()
        if e in [sg.WIN_CLOSED, "Cancel"]:
            window.close()
            return shipment.service
        if 'service' in e.lower():
            window.close()
            return menu_map.get(v['-SERVICE-'])


def get_service_button(num_parcels, service_col, shipment):
    service_name_button = sg.Text(f'{shipment.service.name} \n£{num_parcels * shipment.service.cost}',
                                  background_color=service_col, enable_events=True,
                                  k=f'-{shipment.shipment_name_printable.upper()}_SERVICE-', **shipment_params)
    return service_name_button


def get_parcels_button(num_parcels, shipment):
    parcels_button = sg.Text(f'{num_parcels}', k=f'-{shipment.shipment_name_printable.upper()}_BOXES-',
                             enable_events=True,
                             **boxes_params)
    return parcels_button


def get_recip_button(recipient_address_name, shipment):
    recipient_button = sg.Text(recipient_address_name, enable_events=True,
                               k=f'-{shipment.shipment_name_printable.upper()}_RECIPIENT-', **address_params)
    return recipient_button


def get_sender_button(sender_address_name, shipment):
    sender_button = sg.Text(sender_address_name, enable_events=True,
                            k=f'-{shipment.shipment_name_printable.upper()}_SENDER-', **address_params)

    return sender_button


def get_date_button(date_col, date_name, shipment):
    collection_date_button = sg.Text(date_name, background_color=date_col, enable_events=True,
                                     k=f'-{shipment.shipment_name_printable.upper()}_DATE-', **date_params)
    return collection_date_button


def get_contact_frame(config: Config, contact: Contact, address: Address):
    layout = [
        [sg.Text(f'Name:', **address_fieldname_params),
         sg.InputText(f'{contact.name}', key=f'-NAME-', **address_input_params)],

        [sg.Text(f'Email:', **address_fieldname_params),
         sg.InputText(f'{contact.email}', key=f'-EMAIL-', **address_input_params)],

        [sg.Text(f'Telephone:', **address_fieldname_params),
         sg.InputText(f'{contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],

        [get_address_frame(address=address, config=config)],

        [sg.B('Submit', k=f'-SUBMIT-')]
    ]

    # noinspection PyTypeChecker
    frame = sg.Frame(f'Address Finder', layout=layout, k=f'-REMOTE_ADDRESS-', pad=20, font="Rockwell 30",
                     border_width=5, relief=sg.RELIEF_GROOVE,
                     title_location=sg.TITLE_LOCATION_TOP)
    return frame


def get_date_label(collection_date: CollectionDate, config: Config):
    return f'{datetime.strptime(collection_date.date, config.datetime_masks["DT_DB"]):%A\n%B %#d}'
