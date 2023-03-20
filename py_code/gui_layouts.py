from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse

import PySimpleGUI as sg


# boxes
# dates
# address
class UnSoaped:
    def __init__(self, soapy_object):
        [setattr(self, var) for var in vars(soapy_object) if 'soap' not in var.lower()]


class GuiLayout:
    def __init__(self, parent):
        self.parent=parent
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
            'pad':20
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
        customer = self.customer()
        sender = self.sender_frame()
        recipient = self.recipient_frame()
        date_match = self.date()
        parcels = self.parcels()
        service = self.service()
        queue = self.queue_or_book()
        book = self.go()
        # book_frame = sg.Frame('',layout=book,element_justification='center')
        # frames
        bottom_layout = [
            [date_match],
            [parcels],
            [service],
            [queue],
        ]
        bottom_col = sg.Column(layout=bottom_layout, element_justification='center', **self.bottom_col_params)
        bottom_frame = sg.Frame('', layout=[[bottom_col, book]], **self.bottom_frame_params)

        layout = [
            [sender, recipient],
            [customer, bottom_frame],
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
    def customer(self):
        element = sg.Text(f'{self.shipment.shipment_name}', **self.customer_params)
        return element

    def sender_frame(self):
        title = "Sender"
        shipment = self.shipment
        client = shipment.CNFG.client
        sender = self.get_sender_recip()[0]

        layout = [
            [sg.Text(f'Sender Name:', **self.address_fieldname_params),
             sg.InputText(default_text=sender.name, key=f'-{title.upper()}_NAME-', **self.address_input_params)],
            [sg.Text(f'Sender Email:', **self.address_fieldname_params),
             sg.InputText(default_text=sender.email, key=f'-{title.upper()}_EMAIL-', **self.address_input_params)],
            [sg.Text(f'Sender Phone:', **self.address_fieldname_params),
             sg.InputText(default_text=sender.telephone, key=f'-{title.upper()}_PHONE-', **self.address_input_params)],
            [self.address_frame(sender.sender_address.sender_address, 'sender')]
        ]
        k = f'-{title.upper()}-'
        frame = sg.Frame(f'Sender', layout, k=k, **self.send_recip_frame_params)
        return frame

    def recipient_frame(self):
        shipment = self.shipment
        client = shipment.CNFG.client
        recipient = self.get_sender_recip()[1]

        layout = [
            [sg.Text(f'Recipient Name:', **self.address_fieldname_params),
             sg.InputText(default_text=recipient.name, key='-RECIPIENT_NAME-', **self.address_input_params)],
            [sg.Text(f'Recipient Email:', **self.address_fieldname_params),
             sg.InputText(default_text=recipient.email, key='-RECIPIENT_EMAIL-', **self.address_input_params)],
            [sg.Text(f'Recipient Phone:', **self.address_fieldname_params),
             sg.InputText(default_text=recipient.telephone, key='-RECIPIENT_PHONE-', **self.address_input_params)],
            [self.address_frame(recipient.recipient_address, 'recipient')]
        ]
        frame = sg.Frame(f'Recipient', layout, k='-RECIPIENT-', **self.send_recip_frame_params)
        return frame

    def date(self):
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

    def parcels(self):
        shipment = self.shipment
        boxes = shipment.boxes
        if not boxes or int(boxes) < 1:
            boxes = 1
        element = sg.Spin(initial_value=boxes, k='-BOXES-', values=[i for i in range(10)], **self.option_menu_params)

        return element

    def service(self):
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
                self.shipment.service = potential_service
            menu_def.append(potential_service.name)
            services_menu_map.update({chosen_service_hr: potential_service})
        if not chosen_service:
            chosen_service = services[0]
            chosen_service_hr = chosen_service.name
            services_menu_map.update({chosen_service_hr: chosen_service})

        element = sg.Combo(default_value=chosen_service_hr, values=(menu_def), k='-SERVICE-',
                           **self.option_menu_params, enable_events=True)
        self.service_menu_map = services_menu_map
        return element

    def queue_or_book(self):

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

    def address_frame(self, address, mode):
        left = {
            'size': (15, 1),
            'justification': 'center',
        }
        right = {
            'size': (15, 1),
            'justification': 'center',
            # 'expand_x': True,
        }

        shipment = self.shipment
        layout = []
        for attr in shipment.CNFG.db_address_fields:
            human_readable_attr = shipment.CNFG.gui_map.get(attr, attr.title())
            layout.append(
                [sg.Text(human_readable_attr, **self.address_fieldname_params),
                 sg.InputText(default_text=getattr(address, attr, None), k=f'-{mode}_{attr}-'.upper(),
                              **self.address_input_params)])
        frame = sg.Frame("Address", layout, **self.address_frame_params)
        return frame

    def shipment_request_popup(self, shipmenmt_request):
        layout = []
        for attr in vars(shipmenmt_request):
            layout.append([attr])
        element = sg.T("Shipment Request", layout)
        return element

    def go(self):

        element = sg.Button('Go!', **self.go_button_params, k="-GO-")
        return element

    def blank_frame(self):
        return sg.Frame("", [[]], pad=(5, 3), expand_x=True, expand_y=True, border_width=0)

    # methods



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
