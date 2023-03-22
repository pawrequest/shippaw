from dbfread import DBF
from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse

import PySimpleGUI as sg


class GuiLayout:
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self.client = app.client
        self.shipment = app.shipment

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
        shipment_name = self.shipment_name_element()
        sender = self.sender_receiver_frame('sender')
        recipient = self.sender_receiver_frame('recipient')
        date_match = self.date_chooser()
        parcels = self.parcels_spin()
        service = self.service_combo()
        queue = self.queue_or_book_combo()
        ids = self.shipment_ids()

        try:  # to get prices but they don't seem to exist?
            self.shipment.shipment_request = self.initial_request()
        except:
            pass
        book_button = self.go_button()

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
                  [ids, sg.P(),button_frame]
                  ]
        window = sg.Window("A TITLE", layout, finalize=True)
        return window

    # self.theme_chooser()
    def shipment_ids(self):
        dirs={
            'outbound': getattr(self.shipment, 'outbound_id', None),
            'inbound': getattr(self.shipment, 'inbound_id', None)
        }

        layout = []
        for direction, ID in dirs.items():
            layout.append(
                [sg.T(f"{direction.title()}: {ID}" if direction else None, font='Rockwell 20', size=20, border_width=3,
                  justification='center', relief=sg.RELIEF_GROOVE, pad=20, enable_events=True if ID else False, k=f'-{direction.upper()}_ID-')]
            )

        frame = sg.Frame('Shipment IDs', layout, pad=20, element_justification='center',
                         border_width=8,
                         relief=sg.RELIEF_GROOVE, expand_y=True)
        return frame

    def tracking_viewer_window(self, shipment_id):
        client = self.client
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
                courier = tracking['CourierName']
                parcel_title = [f'{tracked_parcel} ({courier}):']
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

    # elements
    def shipment_name_element(self):
        element = sg.Text(f'{self.shipment.shipment_name}', expand_x=True, expand_y=True, justification='center',
                          font='Rockwell 30',
                          border_width=8, relief=sg.RELIEF_GROOVE, )
        return element

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


    #
    # def sender_receiver_frame(self, mode):
    #     title = mode.title()
    #     shipment = self.shipment
    #     sender, recipient = self.get_sender_recip()
    #     obj_to_edit = getattr(shipment, mode)
    #     address = None
    #     if mode == 'sender':
    #         address = sender.sender_address  # debug somethign screwy here, surely?
    #     elif mode == 'recipient':
    #         address = recipient.recipient_address
    #
    #     layout = [
    #         [sg.Text(f'{title} Name:', **self.address_fieldname_params),
    #          sg.InputText(default_text=getattr(obj_to_edit, 'name'), key=f'-{title.upper()}_NAME-',
    #                       **self.address_input_params)],
    #         [sg.Text(f'{title} Email:', **self.address_fieldname_params),
    #          sg.InputText(default_text=getattr(obj_to_edit, 'email'), key=f'-{title.upper()}_EMAIL-',
    #                       **self.address_input_params)],
    #         [sg.Text(f'{title} Phone:', **self.address_fieldname_params),
    #          sg.InputText(default_text=getattr(obj_to_edit, 'telephone'), key=f'-{title.upper()}_PHONE-',
    #                       **self.address_input_params)],
    #         [self.address_frame(address=address, mode=mode)],
    #         # [sg.B("Update", k=f'-UPDATE_{title.upper()}')]
    #     ]
    #     k = f'-{title.upper()}-'
    #     frame = sg.Frame(f'{title}', layout, k=k, pad=20, font="Rockwell 30", border_width=5, relief=sg.RELIEF_GROOVE,
    #                      title_location=sg.TITLE_LOCATION_TOP)
    #     return frame

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
    #
    # def address_frame(self, address, mode):
    #
    #     shipment = self.shipment
    #     layout = []
    #     # (shipment.CNFG.db_address_fields)
    #     db_address_fields = [
    #         'company_name',
    #         'street',
    #         'locality',
    #         'town_city',
    #         'county',
    #         'postal_code',
    #     ]
    #     params = {**self.address_fieldname_params}.copy()
    #
    #     for attr in db_address_fields:
    #         human_readable_attr = self.config.gui_map.get(attr, attr.title())
    #         if attr in ('company_name', 'postal_code'):
    #             # is a button
    #             params.pop('justification', None)
    #             label_text = sg.B(human_readable_attr, k=f'-{mode}_{attr}-', **params)
    #         else:
    #             label_text = sg.Text(human_readable_attr, k=f'-{mode}_{attr}-', **self.address_fieldname_params)
    #         input_box = sg.InputText(default_text=getattr(address, attr, None), k=f'-{mode}_{attr}-'.upper(),
    #                                  **self.address_input_params)
    #         layout.append(([label_text, input_box]))
    #
    #     # layout.append([sg.B("Search", k=f'-{mode.upper()}_SEARCH-')])
    #     frame = sg.Frame(f"{mode.title()} Address", layout, k=f'-{mode.upper()}_ADDRESS-', pad=20, )
    #     return frame

    def combo_popup(self, options_dict: dict) -> object or None:
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

    def date_chooser(self) -> sg.Combo:
        """ PSG Combo to select a despatchbay collection date object
        if match to send_out_date then green, else purple
        """
        send_date = self.shipment.date
        available_dates = self.shipment.available_dates  # dbay objecrts
        datetime_mask = self.config.datetime_masks['DT_DISPLAY']
        self.date_menu_map = {}
        menu_def = []
        chosen_date_db = None
        chosen_date_hr = None
        params = {'pad': (10, 5), 'size': (30), 'readonly': True, }

        for potential_collection_date in available_dates:
            potential_date = parse(potential_collection_date.date)
            potential_date_hr = datetime.strftime(potential_date.date(), datetime_mask)

            if potential_date == send_date:
                potential_date_hr = potential_date_hr
                chosen_date_db = potential_collection_date
                chosen_date_hr = potential_date_hr
                params.update({'background_color': 'green'})
            # to use human readable names in button and retrieve object later
            self.date_menu_map[potential_date_hr] = potential_collection_date
            # self.date_menu_map.update(potential_date_hr=potential_collection_date)
            menu_def.append(potential_date_hr)
        if not chosen_date_db:
            params.update({'background_color': 'purple'})
            chosen_date_db = available_dates[0]
            chosen_date_hr = menu_def[0]
            self.date_menu_map[chosen_date_hr] = chosen_date_db

        self.shipment.date = chosen_date_db
        params.update(
            default_value=chosen_date_hr,
            values=(menu_def),
            k='-DATE-',
        )
        element = sg.Combo(**params)

        return element

    def parcels_spin(self):
        shipment = self.shipment
        boxes = shipment.boxes
        if not boxes or int(boxes) < 1:
            boxes = 1
        element = sg.Combo(default_value=boxes, k='-BOXES-', values=[i for i in range(10)], **self.option_menu_params)

        return element

    def service_combo(self):
        client = self.client
        services = client.get_services()
        services_menu_map = {}
        menu_def = []

        # get services
        chosen_service = None
        chosen_service_hr = None
        for potential_service in services:
            if potential_service.service_id == self.config.service_id:
                chosen_service = potential_service
                chosen_service_hr = chosen_service.name
            menu_def.append(potential_service.name)
            services_menu_map.update({potential_service.name: potential_service})
        if not chosen_service:
            sg.popup("Default service unavailable")
            chosen_service = services[0]
            chosen_service_hr = chosen_service.name

        self.shipment.service = chosen_service
        element = sg.Combo(default_value=chosen_service_hr, values=menu_def, k='-SERVICE-',
                           **self.option_menu_params, enable_events=True)
        self.service_menu_map = services_menu_map
        return element

    def queue_or_book_combo(self):

        shipment = self.shipment
        shipment_type = f'{"return" if self.shipment.is_return else "shipment"}'
        print_or_email = "email" if shipment.is_return else "print"
        menu_def = [
            f'Book and {print_or_email}',
            'Book only',
            'Queue only'
        ]
        element = sg.Combo(default_value=f'Book and {print_or_email}', values=menu_def,
                           k='-QUEUE OR BOOK-', **self.option_menu_params)

        return element

    def go_button(self):
        shipment = self.shipment
        parcels = len(shipment.parcels) if shipment.parcels else int(shipment.boxes)

        price_each = shipment.service.cost

        price_total = f'{parcels * price_each:.2}' if price_each else ''
        element = sg.Button(f'{price_total}\nGo!', k="-GO-", size=(12, 5), enable_events=True,
                            expand_y=True, pad=20, )
        return element

    # methods
    def initial_request(self):
        shipment = self.shipment
        client = self.client
        shipment.parcels = self.get_parcels(shipment.boxes)

        try:
            shipment_request = client.shipment_request(
                service_id=shipment.service.service_id,
                parcels=shipment.parcels,
                client_reference=shipment.shipment_name.replace(r'/', '-'),
                collection_date=shipment.date,
                sender_address=shipment.sender,
                recipient_address=shipment.recipient,
                follow_shipment=True
            )
        except:
            sg.popup_error("Initial import failed")
            return None
        else:
            return shipment_request

    def get_parcels(self, num_parcels):
        # num_parcels = int(num_parcels.split(" ")[0])
        client = self.client
        parcels = []
        for x in range(int(num_parcels)):
            parcel = client.parcel(
                contents="Radios",
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            parcels.append(parcel)
        self.shipment.parcels = parcels
        return parcels


    #
    # def get_sender_recip(self):
    #     shipment = self.shipment
    #     client = shipment.CNFG.client
    #     if shipment.is_return:
    #         recipient = shipment.home_recipient
    #         sender = client.sender(
    #             name=shipment.delivery_contact,
    #             email=shipment.delivery_email,
    #             telephone=shipment.delivery_tel,
    #             sender_address=client.find_address(shipment.delivery_postcode, shipment.search_term)
    #         )
    #     else:
    #         sender = shipment.home_sender
    #
    #         recipient = client.recipient(
    #             name=shipment.delivery_contact,
    #             email=shipment.delivery_email,
    #             telephone=shipment.delivery_tel,
    #             recipient_address=client.find_address(shipment.delivery_postcode, shipment.search_term)
    #         )
    #     shipment.sender, shipment.recipient = sender, recipient
    #     return sender, recipient

    def theme_chooser(self):
        theme_layout = [[sg.Text("See how elements look under different themes by choosing a different theme here!")],
                        [sg.Listbox(values=sg.theme_list(),
                                    size=(20, 12),
                                    key='-THEME LISTBOX-',
                                    enable_events=True)],
                        [sg.Button("Set Theme")]]
        frame = sg.Frame('Themes', layout=theme_layout)
        return frame

    # def blank_frame(self):
    #     return sg.Frame("", [[]], pad=(5, 3), expand_x=True, expand_y=True, border_width=0)

    # def shipment_request_popup(self, shipment_request):
    #     layout = []
    #     for attr in vars(shipment_request):
    #         layout.append([attr])
    #     element = sg.T("Shipment Request", layout)
    #     return element


