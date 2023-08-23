import PySimpleGUI as sg
from PySimpleGUI import Window
from despatchbay.despatchbay_entities import CollectionDate

from core.config import logger
from core.enums import DateTimeMasks
from core.funcs import print_label, collection_date_to_datetime
from gui import keys_and_strings
from gui.gui_params import address_head_params, address_params, \
    boxes_head_params, boxes_params, date_head_params, date_params, default_params, head_params, option_menu_params, \
    shipment_params
from gui.keys_and_strings import SERVICE_STRING, DATE_STRING, ADDRESS_STRING
from shipper.shipment import ShipmentToRequest


def main_window(outbound: bool, shipments: [ShipmentToRequest]):
    logger.info('BULK SHIPPER WINDOW')
    sg.set_options(**default_params)

    return sg.Window('Bulk Shipper',
                     layout=[
                         [headers(outbound)],
                         # [[self.shipment_frame(shipment=shipment)] for shipment in shipments],
                         [[shipment_frame(shipment=shipment, outbound=outbound)] for shipment in shipments],
                         [sg.Button("LETS GO", k=keys_and_strings.GO_SHIP_KEY(), expand_y=True, expand_x=True)]
                     ],
                     finalize=True)


def shipment_frame(shipment: ShipmentToRequest, outbound: bool):
    print_or_email = 'print' if outbound else 'email'

    date_name = DATE_STRING(collection_date=shipment.collection_date)
    sender_address_name = ADDRESS_STRING(address=shipment.sender.sender_address)
    recipient_address_name = ADDRESS_STRING(shipment.recipient.recipient_address)
    num_parcels = len(shipment.parcels)

    row = [
        customer_contact_button(shipment=shipment),
        recipient_button(recipient_address_name=recipient_address_name, shipment=shipment),
        date_button(date_name=date_name, shipment=shipment),
        parcels_button(num_parcels=num_parcels, shipment=shipment),
        service_button(num_parcels=num_parcels, shipment=shipment),
        sg.Checkbox('Book', default=True, k=keys_and_strings.BOOK_KEY(shipment)),
        sg.Checkbox(f'{print_or_email}', default=True, k=keys_and_strings.PRINT_EMAIL_KEY(shipment)),
        sg.Button('Drop-off', k=keys_and_strings.DROPOFF_KEY(shipment)),
        sg.Button('remove', k=keys_and_strings.REMOVE_KEY(shipment))
    ]

    if not outbound:
        row.insert(1, sender_button(sender_address_name=sender_address_name, shipment=shipment))

    layout = [row]

    return sg.Frame('', layout=layout, k=keys_and_strings.SHIPMENT_KEY(shipment))


def headers(outbound: bool):
    heads = [
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

    if not outbound:
        heads.insert(1, sg.T('Sender', **address_head_params))

    return heads


def post_book(shipments: [ShipmentToRequest]):
    headers = []
    frame = results_frame(shipments=shipments)
    window2 = sg.Window('Booking Results:', layout=[[frame]])
    while True:
        e2, v2 = window2.read()
        if e2 in [sg.WIN_CLOSED, 'Exit']:
            break
        if 'reprint' in e2.lower():
            ship_in_play: ShipmentToRequest = next((shipment for shipment in shipments if
                                                    shipment.shipment_name_printable.lower() in e2.lower()))
            print_label(ship_in_play)

    window2.close()


def results_frame(shipments: [ShipmentToRequest]):
    params = {
        'expand_x': True,
        'expand_y': True,
        'size': (25, 2),
    }

    result_layout = []
    for shipment in shipments:
        num_boxes = len(shipment.parcels)
        ship_res = [
            sg.Text(shipment.shipment_request.client_reference, **params),
            sg.Text(shipment.shipment_return.recipient_address.recipient_address.street, **params),
            sg.Text(SERVICE_STRING(num_boxes=num_boxes, service=shipment.service), **params),
        ]

        if shipment.printed:
            ship_res.extend([sg.Text('Shipment Printed', **params),
                             sg.Button('Reprint Label',
                                       key=keys_and_strings.REPRINT_KEY(shipment), **params)])
        if shipment.logged_to_commence:
            ship_res.append(sg.Text('Shipment ID Logged to Commence', **params))
        # result_layout.append([sg.Frame('', layout=[ship_res])])
        result_layout.append(ship_res)
        # result_layout.append([sg.Text('')])
    return sg.Frame('', vertical_alignment="c", layout=result_layout, element_justification='center')


def new_parcels_popup(location):
    # new_boxes = sg.popup_get_text("Enter a number")
    layout = [
        [sg.Combo(values=[i for i in range(1, 10)], enable_events=True, expand_x=True, readonly=True,
                  default_value=1,
                  k=keys_and_strings.BOX_KEY())]
    ]
    return sg.Window('', layout=layout, location=location, relative_location=(-50, -50))


def new_service_popup(menu_map: dict, default_service: str, location):
    men_def = [k for k in menu_map.keys()]

    layout = [[sg.Combo(k='-SERVICE-', values=men_def, enable_events=True, default_value=default_service,
                        **option_menu_params)]]
    window = Window('Select a service', layout=layout, location=location, relative_location=(-100, -50))

    while True:
        e, v = window.read()
        if e == '-SERVICE-':
            window.close()
            return menu_map.get(v['-SERVICE-'])
        window.close()
        return None

    # return f'{datetime.strptime(collection_date.date, config.datetime_masks["DT_DB"]):%A\n%B %#d}'


def service_button(num_parcels, shipment):
    service_col = 'green' if shipment.default_service_matched else 'maroon4'
    service_name_button = sg.Text(f'{shipment.service.name} \n£{(num_parcels * shipment.service.cost):.2f}',
                                  background_color=service_col, enable_events=True,
                                  k=keys_and_strings.SERVICE_KEY(shipment), **shipment_params)
    return service_name_button


def parcels_button(num_parcels, shipment):
    return sg.Text(f'{num_parcels}', k=keys_and_strings.BOXES_KEY(shipment), enable_events=True, **boxes_params)


def recipient_button(recipient_address_name, shipment):
    recipient_button = sg.Text(recipient_address_name, enable_events=True,
                               k=keys_and_strings.RECIPIENT_KEY(shipment), **address_params)
    return recipient_button


def sender_button(sender_address_name, shipment) -> sg.Text:
    sender_button = sg.Text(sender_address_name, enable_events=True,
                            k=keys_and_strings.SENDER_KEY(shipment), **address_params)

    return sender_button


def customer_contact_button(shipment):
    return sg.T(f'{shipment.contact_name}\n{shipment.customer_printable}', enable_events=True,
                k=keys_and_strings.CUSTOMER_KEY(shipment), **shipment_params)


def date_button(date_name, shipment):
    date_col = 'green' if shipment.date_matched else 'maroon4'
    collection_date_button = sg.Text(date_name, background_color=date_col, enable_events=True,
                                     k=keys_and_strings.DATE_KEY(shipment), **date_params)
    return collection_date_button


def new_date_selector(shipment: ShipmentToRequest, popup_location) -> CollectionDate:
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
