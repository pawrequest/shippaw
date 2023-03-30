import PySimpleGUI as sg


class GuiLayout:
    def __init__(self):

        # shared gui element parameters
        self.default_params = {
            'font': 'Rockwell 14',
            'element_padding': (25, 5),
            'border_width': 3,
        }

        self.address_input_params = {
            'size': (18, 1),
            'justification': 'left',
            'expand_x': True,
            'pad': (20, 8),
        }

        self.address_fieldname_params = {
            'size': (15, 1),
            'justification': 'center',
            'pad': (20, 8),
        }

        self.option_menu_params = {
            'pad': (10, 5),
            'size': (30, 1),
            'readonly': True,
        }

    # windows
    def main_window(self):
        sg.set_options(**self.default_params)
        # elements
        shipment_name = shipment_name_element()
        sender = self.sender_receiver_frame('sender')
        recipient = self.sender_receiver_frame('recipient')
        # todo get addresses before dates
        date_match = date_chooser()
        parcels = self.parcels_spin()
        service = self.service_combo()
        queue = self.queue_or_book_combo()
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
        window = sg.Window("A TITLE", layout, finalize=True)
        return window

    # elements

    def sender_receiver_frame(self, mode):
        title = mode.title()
        layout = [
            [sg.Text(f'Name:', **self.address_fieldname_params),
             sg.InputText(key=f'-{title.upper()}_NAME-', **self.address_input_params)],

            [sg.Text(f'Email:', **self.address_fieldname_params),
             sg.InputText(key=f'-{title.upper()}_EMAIL-', **self.address_input_params)],

            [sg.Text(f'Telephone:', **self.address_fieldname_params),
             sg.InputText(key=f'-{title.upper()}_TELEPHONE-', **self.address_input_params)],

            [self.address_frame(mode=mode)],
        ]

        k = f'-{title.upper()}-'
        # noinspection PyTypeChecker
        frame = sg.Frame(f'{title}', layout, k=k, pad=20, font="Rockwell 30", border_width=5, relief=sg.RELIEF_GROOVE,
                         title_location=sg.TITLE_LOCATION_TOP)
        return frame

    def address_frame(self, mode):
        layout = []
        address_fields = [
            'company_name',
            'street',
            'locality',
            'town_city',
            'county',
            'postal_code',
        ]
        params = self.address_fieldname_params.copy()

        for attr in address_fields:
            key = f'-{mode}_{attr}-'.upper()
            key_hr = attr.title().replace('_', ' ')

            if attr in ('company_name', 'postal_code'):
                # is a button
                params.pop('justification', None)
                label_text = sg.B(key_hr, k=key.lower(), **params)
            else:
                label_text = sg.Text(key_hr, k=key.lower(), **self.address_fieldname_params)

            input_box = sg.InputText(k=key, **self.address_input_params)
            layout.append([label_text, input_box])

        frame = sg.Frame(f"{mode.title()} Address", layout, k=f'-{mode.upper()}_ADDRESS-', pad=20, )
        return frame

    def parcels_spin(self):
        element = sg.Combo(k='-BOXES-', values=[i for i in range(10)], **self.option_menu_params)

        return element

    def service_combo(self):

        element = sg.Combo(k='-SERVICE-', values=[],
                           **self.option_menu_params, enable_events=True)
        return element

    def queue_or_book_combo(self):
        element = sg.Combo(values=[],
                           k='-QUEUE_OR_BOOK-', **self.option_menu_params)

        return element


def shipment_ids_frame():
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


def shipment_name_element():
    element = sg.Text('', expand_x=True, expand_y=True, justification='center',
                      font='Rockwell 30',
                      border_width=8, relief=sg.RELIEF_GROOVE, k='-SHIPMENT_NAME-')
    return element


def combo_popup(options_dict: dict) -> object or None:
    """
    Creates a popup window with a sg.Combo() selector and waits for the user to select an option.
    Returns the selected option.
    :param options_dict: human readable keys and object-friendly values
    :return: the selected object
    """
    selected_option = None
    default_value = list(options_dict.keys())[0]
    layout = [
        [sg.Combo(list(options_dict.keys()), default_value=default_value, enable_events=True, readonly=True,
                  k='select')],
    ]

    window = sg.Window('Address Selector', layout)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            # User closed the window
            break
        elif event == 'select':
            if values:
                selected_option = values['select']
            break

    window.close()

    return options_dict.get(selected_option)


def date_chooser() -> sg.Combo:
    """ PSG Combo to select a despatchbay collection date object
    if match to send_out_date then green, else purple
    """

    element = sg.Combo(values=[], pad=(10, 5), size=30, readonly=True, k='-DATE-')

    return element


def go_button():
    element = sg.Button(f'Go!', k="-GO-", size=(12, 5), enable_events=True,
                        expand_y=True, pad=20, )
    return element


def theme_chooser():
    theme_layout = [[sg.Text("See how elements look under different themes by choosing a different theme here!")],
                    [sg.Listbox(values=sg.theme_list(),
                                size=(20, 12),
                                key='-THEME LISTBOX-',
                                enable_events=True)],
                    [sg.Button("Set Theme")]]
    frame = sg.Frame('Themes', layout=theme_layout)
    return frame
