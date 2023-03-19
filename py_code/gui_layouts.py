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
        self.shipment = parent.shipment
        self.layout = None
        self.default_params = {
            'font': 'Rockwell 14',
            'element_padding': (25, 5),
            'border_width': 3,

        }
        self.go_button = {
            # 'expand_y': True,
            # 'expand_x': True,
            # 'pad': 40,
            'size': (12, 5),
            'border_width': 5,
            'button_color': "aquamarine4",
            'enable_events': True,
        }
        self.option_menu_params = {
            # 'expand_y': True,
            'expand_x': True,
            # 'pad': (20,3) ,
            # 'size': (12, 2),
            'background_color': "aquamarine4",
            # 'enable_events': True,
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
            'enable_events': True,
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
            'expand_x': True
        }
        self.parcels_params = self.option_menu_params.copy()
        self.parcels_params.update(
            expand_x=False,
            k='-PARCELS-',
            size=10,
            # enable_events =True,
        )

    # windows
    def main_window(self):
        sg.set_options(**self.default_params)

        # elements
        customer = self.customer()
        sender = self.sender_frame()
        # sender = self.sender_recipient_frame('sender')
        # recipient = self.sender_recipient_frame('recipient')
        recipient = self.recipient_frame()
        date_match = self.date()
        parcels = self.parcels()
        service = self.service()
        queue = self.queue_or_book()
        book = self.go()

        # frames
        bottom_layout = [
            [date_match],
            [parcels, service],
            [queue],
        ]
        bottom_frame = sg.Frame("", bottom_layout, **self.bottom_frame_params)

        layout = [
            [customer],
            [sender, recipient],
            [bottom_frame, book],
            [sg.B("Change")],
        ]

        # temporary layout
        # layout = [[self.date_match()]]
        # window = sg.Window("A TITLE", layout, finalize=True)

        # windows
        window = sg.Window("A TITLE", layout, finalize=True)
        return window

    # elements
    def customer(self):
        params = {
            # 'size':(,1),
            'justification': 'left',
            'font': 'Rockwell 24',
            'border_width': 4,
            'expand_x': True,
            'pad': (60, 20)
        }
        element = sg.Text(f'{self.shipment.customer}', **params)
        return element

    def sender_frame(self):
        title = "Sender"
        shipment = self.shipment
        client = shipment.CNFG.client
        sender = self.get_sender_recip()[0]

        layout = [
            [sg.Text(f'Sender Name:', **self.address_fieldname_params),
             sg.InputText(default_text=sender.name, key=f'{title.lower()}_name', **self.address_input_params)],
            [sg.Text(f'Sender Email:', **self.address_fieldname_params),
             sg.InputText(default_text=sender.email, key=f'{title.lower()}_email', **self.address_input_params)],
            [sg.Text(f'Sender Phone:', **self.address_fieldname_params),
             sg.InputText(default_text=sender.telephone, key=f'{title.lower()}_phone', **self.address_input_params)],
            [self.address_frame(sender.sender_address.sender_address)]
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
             sg.InputText(default_text=recipient.name, key='-RECIPIENT NAME-', **self.address_input_params)],
            [sg.Text(f'Recipient Email:', **self.address_fieldname_params),
             sg.InputText(default_text=recipient.email, key='-RECIPIENT EMAIL-', **self.address_input_params)],
            [sg.Text(f'Recipient Phone:', **self.address_fieldname_params),
             sg.InputText(default_text=recipient.telephone, key='-RECIPIENT PHONE-', **self.address_input_params)],
            [self.address_frame(recipient.recipient_address)]
        ]
        frame = sg.Frame(f'Recipient', layout, k='-Recipient-', **self.send_recip_frame_params)
        return frame

    def date(self):
        send_date = self.shipment.send_out_date
        available_dates = self.shipment.available_dates  # dbay objecrts
        datetime_mask = self.shipment.CNFG.datetime_masks['DT_DISPLAY']

        menu_def = []
        chosen_date_db = None
        chosen_date_hr = None

        for potential_collection_date in available_dates:
            potential_date = parse(potential_collection_date.date)
            potential_date_hr = datetime.strftime(potential_date.date(), datetime_mask)

            if potential_date == send_date:
                potential_date_hr = f"Send Date Match : {potential_date_hr}"  # string
                chosen_date_db = potential_collection_date
                chosen_date_hr = potential_date_hr
            menu_def.append(potential_date_hr)
        if not chosen_date_db:
            chosen_date_db = available_dates[0]
            chosen_date_hr = f"Earliest Collection: {menu_def[0]}"
        self.shipment.date = chosen_date_db

        # element = sg.OptionMenu(default_value=chosen_date_hr, size=40, values=(menu_def), k='-DATE-', **self.option_menu_params)
        element = sg.Combo(default_value=chosen_date_hr, readonly=True, size=40, values=(menu_def), k='-DATE-',
                           **self.option_menu_params)

        return element

    def parcels(self):
        boxes = self.shipment.boxes
        client = self.shipment.CNFG.client
        if not boxes or int(boxes) < 1:
            boxes = 1
        parcels = []
        for x in range(int(boxes)):
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

        men_def = [str(i + 1) for i in range(3)]
        men_def.append("More")

        element = sg.OptionMenu(default_value=f'{len(parcels)} Boxes', values=men_def, **self.parcels_params)

        return element

    def service(self):

        client = self.shipment.CNFG.client
        services = client.get_services()
        menu_def = []

        # get services
        chosen_service = None
        chosen_service_hr = None
        for s in services:
            if s.service_id == self.shipment.CNFG.service_id:
                chosen_service = s
                chosen_service_hr = f'Default: {chosen_service.name}'
                self.shipment.service = s
            menu_def.append(s.name)
        if not chosen_service:
            chosen_service = services[0]
            chosen_service_hr = chosen_service.name

        element = sg.OptionMenu(default_value=chosen_service_hr, values=(menu_def), k='-SERVICE-',
                                **self.option_menu_params)

        return element

    def queue_or_book(self):

        shipment = self.shipment
        shipment_type = f'{"return" if self.shipment.is_return else "shipment"}'
        queue = f'Queue {shipment_type}'
        book = f'Book and {"email" if shipment.is_return else "print"} label '
        menu_def = [
            queue, book,
        ]
        element = sg.OptionMenu(default_value=book, values=menu_def, k='-QUEUE OR BOOK-', **self.option_menu_params)

        return element

    def sender_recipient_frame(self, mode):
        shipment = self.shipment
        sender, recipient = self.get_sender_recip()
        title = mode.title()
        if mode == 'sender':
            address = sender.sender_address
        elif mode == 'recipient':
            address = recipient.recipient_address
        else:
            raise TypeError
        layout = [
            [sg.Text(f'{title} Name:', **self.address_fieldname_params),
             sg.InputText(key=f'{title.lower()}_name', default_text="222", **self.address_input_params)],
            [sg.Text(f'{title} Email:', **self.address_fieldname_params),
             sg.InputText(key=f'{title.lower()}_email', **self.address_input_params)],
            [sg.Text(f'{title} Phone:', **self.address_fieldname_params),
             sg.InputText(key=f'{title.lower()}_phone', **self.address_input_params)],
            [self.address_frame(address)]
            # todo this is lies mode
        ]
        k = f'-{title.upper()}-'
        frame = sg.Frame(f'{title}', layout, k=k, **self.send_recip_frame_params)
        return frame

    def address_frame(self, address):
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
            layout.append([sg.Text(human_readable_attr, **self.address_fieldname_params),
                           sg.InputText(default_text=getattr(address, attr, None), **self.address_input_params)])
        frame = sg.Frame("Address", layout, **self.address_frame_params)
        return frame

    def go(self):

        element = sg.Button('Go!', **self.go_button, k="-GO-")
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
