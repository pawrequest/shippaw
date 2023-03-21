from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse

import PySimpleGUI as sg


class GuiLayout:
    def __init__(self, parent):
        self.parent = parent
        self.shipment = parent.shipment
        self.layout = None
        self.default_params = {
            'font': 'Rockwell 14',
            'element_padding': (25, 5),
            'border_width': 3,
            'background_color': 'aquamarine'

        }

        self.send_recip_frame_params = {
            'pad': 20,
            'font': "R♣ockwell 30",
            'title_location': sg.TITLE_LOCATION_TOP,
            # 'size': (500, 500),
        }

        self.address_input_params = {
            'size': (18, 1),
            'justification': 'left',
            'expand_x': True,
            'pad': (20, 8),
            # 'enable_events': True,
        }

        self.address_fieldname_params = {
            'size': (15, 1),
            'justification': 'center',
            # 'expand_x': True,
            'pad': (20, 8),
        }

        self.address_frame_params = {
            'pad': 20,
            # 'size': (450, 400)
        }

        self.bottom_frame_params = {
            # 'size':(250,160)
            # 'expand_x': True
            'pad': 20
        }

        self.customer_params = {
            'expand_x': True,
            # 'size':(,1),
            'justification': 'left',
            'font': 'Rockwell 24',
            'border_width': 4,
            # 'pad': ((20,20), 20)
        }

        self.option_menu_params = {
            # 'expand_y': True,
            # 'expand_x': True,
            'pad': (10, 5),
            'size': (25, 1),
            'background_color': "aquamarine4",
            # 'enable_events': True,
            'readonly': True,
            # 'text_justification':'center'

        }

        self.go_button_params = {
            # 'expand_y': True,
            # 'expand_x': True,
            # 'pad': 40,
            'size': (12, 5),
            # 'border_width': 5,
            'button_color': "aquamarine4",
            'enable_events': True,
            'expand_x': True,
            'expand_y': True,
            'pad': 20,
        }

        self.bottom_col_params = {
            # 'size': (300,160),
            'pad': 20,
            'expand_x': True,
        }
        # self.parcels_params = self.option_menu_params.copy()
        # self.parcels_params.update(
        #     expand_x=False,
        #     k='-PARCELS-',
        #     size=10,
        #     # enable_events =True,
        # )

    # windows
    def main_window(self):
        sg.set_options(**self.default_params)
        sg.theme('DarkTeal6')
        # elements
        shipment_name = self.shipment_name_frame()
        sender = self.sender_receiver_frame('sender')
        recipient = self.sender_receiver_frame('recipient')
        date_match = self.date_chooser()
        parcels = self.parcels_spin()
        service = self.service_combo()
        queue = self.queue_or_book_combo()
        try:
            self.shipment.shipment_request = self.initial_request()
        except:
            ...
        book_button = self.go_button()
        # book_frame = sg.Frame('',layout=book,element_justification='center')
        # frames
        bottom_layout = [
            [date_match],
            [parcels],
            [service],
            [queue],
        ]
        bottom_col = sg.Column(layout=bottom_layout, element_justification='center', **self.bottom_col_params)
        bottom_frame = sg.Frame('', layout=[[bottom_col, book_button]], **self.bottom_frame_params)

        layout = [
            [sender, recipient],
            [shipment_name, bottom_frame],
        ]

        # # temporarylayout
        # layout = [[bottom_frame]]
        # window = sg.Window("A TITLE", layout, finalize=True)
        #
        # return window

        # windows
        window = sg.Window("A TITLE", layout, finalize=True)
        return window

    # elements
    def shipment_name_frame(self):
        element = sg.Text(f'{self.shipment.shipment_name}', **self.customer_params)
        return element

    def sender_receiver_frame(self, mode):
        title = mode.title()
        shipment = self.shipment
        client = shipment.CNFG.client
        sender, recipient = self.get_sender_recip()
        obj_to_edit = getattr(shipment, mode)
        address = None
        if mode == 'sender':
            address = sender.sender_address.sender_address
        elif mode == 'recipient':
            address = recipient.recipient_address

        layout = [
            [sg.Text(f'{title} Name:', **self.address_fieldname_params),
             sg.InputText(default_text=getattr(obj_to_edit, 'name'), key=f'-{title.upper()}_NAME-',
                          **self.address_input_params)],
            [sg.Text(f'{title} Email:', **self.address_fieldname_params),
             sg.InputText(default_text=getattr(obj_to_edit, 'email'), key=f'-{title.upper()}_EMAIL-',
                          **self.address_input_params)],
            [sg.Text(f'{title} Phone:', **self.address_fieldname_params),
             sg.InputText(default_text=getattr(obj_to_edit, 'telephone'), key=f'-{title.upper()}_PHONE-',
                          **self.address_input_params)],
            [self.address_frame(address=address, mode=mode)],
            # [sg.B("Update", k=f'-UPDATE_{title.upper()}')]
        ]
        k = f'-{title.upper()}-'
        frame = sg.Frame(f'{title}', layout, k=k, **self.send_recip_frame_params)
        return frame

    def address_frame(self, address, mode):

        shipment = self.shipment
        layout = []
        # (shipment.CNFG.db_address_fields)
        db_address_fields = [
            'company_name',
            'street',
            'locality',
            'town_city',
            'county',
            'postal_code',
        ]
        params = {**self.address_fieldname_params}.copy()

        for attr in db_address_fields:
            human_readable_attr = shipment.CNFG.gui_map.get(attr, attr.title())
            if attr in ('company_name', 'postal_code'):
                # is a button
                params.pop('justification', None)
                label_text = sg.B(human_readable_attr, k=f'-{mode}_{attr}-', **params)
            else:
                label_text = sg.Text(human_readable_attr, k=f'-{mode}_{attr}-', **self.address_fieldname_params)
            input_box = sg.InputText(default_text=getattr(address, attr, None), k=f'-{mode}_{attr}-'.upper(),
                                     **self.address_input_params)
            layout.append(([label_text, input_box]))

        # layout.append([sg.B("Search", k=f'-{mode.upper()}_SEARCH-')])
        frame = sg.Frame(f"{mode.title()} Address", layout, **self.address_frame_params, k=f'-{mode.upper()}_ADDRESS-')
        return frame

    def combo_popup(self, options_dict):
        """
        Creates a popup window with a sg.Combo() selector and waits for the user to select an option.
        Returns the selected option.
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

    def date_chooser(self):
        send_date = self.shipment.send_out_date
        available_dates = self.shipment.available_dates  # dbay objecrts
        datetime_mask = self.shipment.CNFG.datetime_masks['DT_DISPLAY']
        self.date_menu_map = {}
        menu_def = []
        chosen_date_db = None
        chosen_date_hr = None
        params = self.option_menu_params.copy()

        for potential_collection_date in available_dates:
            potential_date = parse(potential_collection_date.date)
            potential_date_hr = datetime.strftime(potential_date.date(), datetime_mask)

            if potential_date == send_date:
                potential_date_hr = potential_date_hr
                chosen_date_db = potential_collection_date
                chosen_date_hr = potential_date_hr
            # to use human readable names in button and retrieve object later
            self.date_menu_map[potential_date_hr] = potential_collection_date
            # self.date_menu_map.update(potential_date_hr=potential_collection_date)
            menu_def.append(potential_date_hr)
        if not chosen_date_db:
            params.update({'background_color': 'firebrick'})
            chosen_date_db = available_dates[0]
            chosen_date_hr = menu_def[0]
            self.date_menu_map[chosen_date_hr] = chosen_date_db

        self.shipment.date = chosen_date_db
        params.update(
            default_value=chosen_date_hr,
            values=(menu_def),
            k='-DATE-',
        )
        # element = sg.OptionMenu(default_value=chosen_date_hr, size=40, values=(menu_def), k='-DATE-', **self.option_menu_params)
        element = sg.Combo(**params)

        return element

    def parcels_spin(self):
        shipment = self.shipment
        boxes = shipment.boxes
        if not boxes or int(boxes) < 1:
            boxes = 1
        element = sg.Spin(initial_value=boxes, k='-BOXES-', values=[i for i in range(10)], **self.option_menu_params)

        return element

    def service_combo(self):
        client = self.shipment.CNFG.client
        services = client.get_services()
        services_menu_map = {}
        menu_def = []

        # get services
        chosen_service = None
        chosen_service_hr = None
        for potential_service in services:

            if potential_service.service_id == self.shipment.CNFG.service_id:
                chosen_service = potential_service
                chosen_service_hr = chosen_service.name
            menu_def.append(potential_service.name)
            services_menu_map.update({chosen_service_hr: potential_service})
        if not chosen_service:
            chosen_service = services[0]
            chosen_service_hr = chosen_service.name
            services_menu_map.update({chosen_service_hr: chosen_service})

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
        element = sg.Button(f'{price_total}\nGo!', **self.go_button_params, k="-GO-")
        return element

    # methods
    def initial_request(self):
        shipment = self.shipment
        client = shipment.CNFG.client
        shipment.parcels = self.get_parcels(shipment.boxes)

        shipment_request = client.shipment_request(
            service_id=shipment.service.service_id,
            parcels=shipment.parcels,
            client_reference=shipment.label_text,
            collection_date=shipment.date,
            sender_address=shipment.sender,
            recipient_address=shipment.recipient,
            follow_shipment=True
        )
        return shipment_request

    def get_parcels(self, num_parcels):
            # num_parcels = int(num_parcels.split(" ")[0])
            client = self.shipment.CNFG.client
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

    def get_sender_recip(self):
        shipment = self.shipment
        client = shipment.CNFG.client
        if shipment.is_return:
            recipient = shipment.amherst_recipient
            sender = client.sender(
                name=shipment.delivery_contact,
                email=shipment.delivery_email,
                telephone=shipment.delivery_tel,
                sender_address=client.find_address(shipment.delivery_postcode, shipment.search_term)
            )
        else:
            sender = shipment.amherst_sender

            recipient = client.recipient(
                name=shipment.delivery_contact,
                email=shipment.delivery_email,
                telephone=shipment.delivery_tel,
                recipient_address=client.find_address(shipment.delivery_postcode, shipment.search_term)
            )
        shipment.sender, shipment.recipient = sender, recipient
        return sender, recipient

    # def blank_frame(self):
    #     return sg.Frame("", [[]], pad=(5, 3), expand_x=True, expand_y=True, border_width=0)

    # def shipment_request_popup(self, shipment_request):
    #     layout = []
    #     for attr in vars(shipment_request):
    #         layout.append([attr])
    #     element = sg.T("Shipment Request", layout)
    #     return element
