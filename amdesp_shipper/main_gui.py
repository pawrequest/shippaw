from datetime import datetime

import PySimpleGUI as sg
from PySimpleGUI import Window
from dateutil.parser import parse

from amdesp_shipper.config import Config, get_amdesp_logger
from despatchbay.despatchbay_entities import Address, CollectionDate, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp_shipper.enums import DateTimeMasks, FieldsList
from amdesp_shipper.gui_params import address_fieldname_params, address_head_params, address_input_params, address_params, \
    boxes_head_params, boxes_params, date_head_params, date_params, default_params, head_params, option_menu_params, \
    shipment_params
from amdesp_shipper.shipment import Shipment

logger = get_amdesp_logger()


class Gui:
    def __init__(self, config: Config, client: DespatchBaySDK):
        self.window = None
        self.event = None
        self.values = None
        self.config = config
        self.client = client


class MainGui(Gui):
    def bulk_shipper_window(self, shipments: [Shipment]):
        logger.info('BULK SHIPPER WINDOW')
        if self.config.sandbox:
            sg.theme('Tan')
        else:
            sg.theme('Dark Blue')

        sg.set_options(**default_params)

        return sg.Window('Bulk Shipper',
                         layout=[
                             [self.get_headers()],
                             [self.get_shipment_frame(shipment=shipment) for shipment in shipments],
                             [sg.Button("LETS GO", k='-GO_SHIP-', expand_y=True, expand_x=True)]
                         ],
                         finalize=True)

    def get_shipment_frame(self, shipment: Shipment):
        print_or_email = 'print' if self.config.outbound else 'email'

        date_name = self.get_date_label(collection_date=shipment.collection_date)
        sender_address_name = self.get_address_button_string(address=shipment.sender.sender_address)
        recipient_address_name = self.get_address_button_string(shipment.recipient.recipient_address)
        num_parcels = len(shipment.parcels)

        row = [
            sg.T(f'{shipment.contact_name}\n{shipment.customer}', **shipment_params),
            get_recip_button(recipient_address_name=recipient_address_name, shipment=shipment),
            get_date_button(date_name=date_name, shipment=shipment),
            get_parcels_button(num_parcels=num_parcels, shipment=shipment),
            get_service_button(num_parcels=num_parcels, shipment=shipment),
            sg.Checkbox('Add', default=True, k=f'-{shipment.shipment_name_printable}_ADD-'.upper()),
            sg.Checkbox('Book', default=True, k=f'-{shipment.shipment_name_printable}_BOOK-'.upper()),
            sg.Checkbox(f'{print_or_email}', default=True,
                        k=f'-{shipment.shipment_name_printable}_PRINT_EMAIL-'.upper()),
            sg.Button('remove', k=f'-{shipment.shipment_name_printable}_REMOVE-'.upper())
        ]

        if not self.config.outbound:
            row.insert(1, get_sender_button(sender_address_name=sender_address_name,
                                         shipment_name=shipment.shipment_name_printable))


        layout = [row]

        return sg.Frame('', layout=layout, k=f'-SHIPMENT_{shipment.shipment_name_printable}-'.upper())

    def get_headers(self):
        headers = [
            # sg.Sizer(30, 0),
            sg.T('Contact / Customer', **head_params),
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

        if not self.config.outbound:
            headers.insert(1, sg.T('Sender', **address_head_params))


        return headers

    def get_service_string(self, num_boxes: int, service: Service):
        return f'{service.name}\n{num_boxes * service.cost}'

    @staticmethod
    def booked_shipments_frame(shipments: [Shipment]):
        params = {
            'expand_x': True,
            'expand_y': True,
            'size': (25, 2)
        }

        result_layout = []
        for shipment in shipments:
            num_boxes = len(shipment.parcels)
            ship_res = [sg.Text(shipment.shipment_request.client_reference, **params),
                        sg.Text(shipment.shipment_return.recipient_address.recipient_address.street, **params),
                        sg.Text(
                            f'{shipment.service.name} - {num_boxes} boxes = £{num_boxes * shipment.service.cost}:.2')]

            if shipment.printed:
                ship_res.append(sg.Text('Shipment Printed'))
            if shipment.logged_to_commence:
                ship_res.append(sg.Text('Shipment ID Logged to Commence'))
            # result_layout.append([sg.Frame('', layout=[ship_res])])
            result_layout.append(ship_res)
            # result_layout.append([sg.Text('')])
        return sg.Frame('', layout=result_layout)

    @staticmethod
    def new_date_selector(shipment: Shipment, location):
        location = location
        menu_map = shipment.date_menu_map
        men_def = [k for k in menu_map.keys()]
        datetime_mask = DateTimeMasks.DISPLAY.value
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

    def post_book(self, shipments: [Shipment]):
        headers = []
        frame = self.booked_shipments_frame(shipments=shipments)
        window2 = sg.Window('Booking Results:', layout=[[frame]])
        while True:
            e2, v2 = window2.read()
            if e2 in [sg.WIN_CLOSED, 'Exit']:
                window2.close()

            window2.close()
            break

    def tracking_viewer_window(self, shipment_id):
        client = self.client
        logger.info(f'TRACKING VIEWER GUI - SHIPMENT ID: {shipment_id}')
        shipment_return = client.get_shipment(shipment_id)
        tracking_numbers = [parcel.tracking_number for parcel in shipment_return.parcels]
        tracking_d = {}
        layout = []
        for tracked_parcel in tracking_numbers:
            parcel_layout = []
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

    @staticmethod
    def get_new_parcels_window(location):
        # new_boxes = sg.popup_get_text("Enter a number")
        layout = [
            [sg.Combo(values=[i for i in range(1, 10)], enable_events=True, expand_x=True, readonly=True,
                      default_value=1,
                      k='BOX')]
        ]
        return sg.Window('', layout=layout, location=location, relative_location=(-50, -50))

    @staticmethod
    def new_service_selector(menu_map: dict, default_service: str, location):
        men_def = [k for k in menu_map.keys()]

        layout = [[sg.Combo(k='-SERVICE-', values=men_def, enable_events=True, default_value=default_service,
                            **option_menu_params)]]
        window = Window('Select a service', layout=layout, location=location, relative_location=(-100, -50))

        while True:
            e, v = window.read()
            if e in [sg.WIN_CLOSED, "Cancel"]:
                break
            if 'service' in e.lower():
                window.close()
                return menu_map.get(v['-SERVICE-'])
            window.close()
            return None

    # return f'{datetime.strptime(collection_date.date, config.datetime_masks["DT_DB"]):%A\n%B %#d}'

    def get_date_label(self, collection_date: CollectionDate):
        return f'{datetime.strptime(collection_date.date, DateTimeMasks.DB.value):{DateTimeMasks.button_label.value}}'
        # return f'{datetime.strptime(collection_date.date, DateTimeMasks.db.value):%A\n%B %#d}'

    @staticmethod
    def get_address_button_string(address: Address):
        # return f'{address.company_name}\n{address.street}' if address.company_name else address.street
        return f'{address.company_name if address.company_name else "< no company name >"}\n{address.street}'


def get_service_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
    """ gets available shipping services for shipment sender and recipient
    builds menu_def of potential services and if any matches service_id specified in config.toml then select it by default
     return a dict of menu_def and default_value"""
    services = client.get_services()
    # todo get AVAILABLE services needs a request
    # services = client.get_available_services()
    shipment.service_menu_map.update({service.name: service for service in services})
    chosen_service = next((service for service in services if service.service_id == config.default_shipping_service.service),
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


def get_address_dict_frame(config: Config, address_dict):
    layout = []
    address_fields = FieldsList.address.value
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


def loading():
    layout = [
        [sg.Text("Loading Shipments")]
    ]

    return sg.Window('Loading', layout, modal=True, disable_close=True, finalize=True)


def get_service_button(num_parcels, shipment):
    service_col = 'green' if shipment.default_service_matched else 'maroon4'
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


def get_sender_button(sender_address_name, shipment_name: str) -> sg.Text:
    sender_button = sg.Text(sender_address_name, enable_events=True,
                            k=f'-{shipment_name}_SENDER-'.upper(), **address_params)

    return sender_button


def get_date_button(date_name, shipment):
    date_col = 'green' if shipment.date_matched else 'maroon4'
    collection_date_button = sg.Text(date_name, background_color=date_col, enable_events=True,
                                     k=f'-{shipment.shipment_name_printable.upper()}_DATE-', **date_params)
    return collection_date_button

    # noinspection PyTypeChecker

#
# def get_address_frame(address_fields: [], address: Address, index: str = None) -> sg.Frame:
#     layout = []
#     params = address_fieldname_params.copy()
#     input_text = ''
#     for field in address_fields:
#         if index:
#             key = f'-{index}_ADDRESS_{field}-'.upper()
#         else:
#             key = f'-ADDRESS_{field}-'.upper()
#
#         input_text = getattr(address, field)
#         key_for_humans = field.title().replace('_', ' ')
#
#         if field in ('company_name', 'postal_code'):
#             # is a button
#             params.pop('justification', None)
#             label_text = sg.B(key_for_humans, k=key.lower(), **params)
#         else:
#             label_text = sg.Text(key_for_humans, k=key.lower(), **address_fieldname_params)
#
#         input_box = sg.InputText(input_text, k=key.upper(), **address_input_params)
#         layout.append([label_text, input_box])
#
#     frame = sg.Frame('Address', layout, pad=20)
#     return frame

#
# frame = sg.Frame(f'Address Finder', layout=layout, k=f'-REMOTE_ADDRESS-', pad=20, font="Rockwell 30",
#                      border_width=5, relief=sg.RELIEF_GROOVE,
#                      title_location=sg.TITLE_LOCATION_TOP)
#     return frame
