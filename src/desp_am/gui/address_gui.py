import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address, AddressKey
from despatchbay.despatchbay_sdk import DespatchBaySDK

from ..core.entities import Contact, FieldsList
from .gui_params import address_fieldname_params, address_input_params


def address_window(contact: Contact, address: Address, address_as_str, delivery_name: str):
    commence_frame = commence_address_frame(delivery_name=delivery_name, contact_name=contact.name,
                                            address_as_str=address_as_str)
    address_col = sg.Col(layout=[
        [contact_frame(contact=contact)],
        [get_address_frame(address=address)],
        [sg.B('Submit', k=f'-SUBMIT-')]

    ])

    return sg.Window('Manual Address Selector', layout=[[commence_frame, address_col]])


def commence_address_frame(contact_name, delivery_name, address_as_str: str):
    return sg.Frame(title='Address Details From Commence:', layout=[
        [sg.Text(contact_name)],
        [sg.Text(delivery_name)],
        [sg.Text(address_as_str)]
    ])


def contact_frame(contact: Contact):
    layout = [
        [sg.Text(f'Name:', **address_fieldname_params),
         sg.InputText(f'{contact.name}', key=f'-NAME-', **address_input_params)],

        [sg.Text(f'Email:', **address_fieldname_params),
         sg.InputText(f'{contact.email}', key=f'-EMAIL-', **address_input_params)],

        [sg.Text(f'Telephone:', **address_fieldname_params),
         sg.InputText(f'{contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],
    ]
    return sg.Frame("Contact Details", layout=layout)


def address_from_postcode_popup(candidate_keys: list[AddressKey], client: DespatchBaySDK) -> Address:
    """ creates a popup window to allow user to select an address from those at a postcode """
    candidate_dict = {candidate.address: candidate.key for candidate in candidate_keys}

    layout = [[sg.Listbox(list(candidate_dict.keys()), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, expand_x=True,
                          expand_y=True, enable_events=True, size=(50, 20), bind_return_key=True,
                          default_values=candidate_keys[0].address, k='select', auto_size_text=True)]]

    window = sg.Window('Address Selector', layout)
    event, values = window.read()
    window.close()

    if event == 'select':
        address_key = candidate_dict.get(values['select'][0])
        address = client.get_address_by_key(address_key)
        window.close()
        return address


def update_address_from_gui(values: dict, address: Address):
    for field in FieldsList.address.value:
        value = values.get(f'-ADDRESS_{field.upper()}-', None)
        setattr(address, field, value)


def company_name_click(address: Address, customer: str, values: dict):
    update_address_from_gui(values=values, address=address)
    setattr(address, 'company_name', customer)


def get_address_frame(address: Address) -> sg.Frame:
    layout = []
    params = address_fieldname_params.copy()

    for field in FieldsList.address.value:
        key = f'-ADDRESS_{field}-'.upper()

        input_text = getattr(address, field)
        key_for_humans = field.title().replace('_', ' ')

        if field in ('company_name', 'postal_code'):
            # is a button
            params.pop('justification', None)
            legend = sg.B(key_for_humans, k=key.lower(), **params)
        else:
            legend = sg.Text(key_for_humans, k=key.lower(), **address_fieldname_params)

        input_box = sg.InputText(input_text, k=key.upper(), **address_input_params)
        layout.append([legend, input_box])

    frame = sg.Frame('Address', layout, pad=20)
    return frame


def update_gui_from_address(address: Address, window):
    if address:
        address_dict = {k: v for k, v in vars(address).items() if 'soap' not in k}
        address_dict.pop('country_code', None)
        for k, v in address_dict.items():
            window[f'-ADDRESS_{k.upper()}-'].update(v or '')


def update_contact_from_gui(values: dict, contact: Contact):
    for field in FieldsList.contact.value:
        value = values.get(f'-{field.upper()}-', None)
        setattr(contact, field, value)


def address_from_gui(shipment: 'ShipmentInput', address: Address, contact: Contact, client:DespatchBaySDK) -> Address | None:
    """ Gui loop, takes an address and shipment for contact details,
    allows editing / replacing address and contact """
    window = address_window(delivery_name=shipment.delivery_name, contact=contact, address=address,
                            address_as_str=shipment.address_as_str)
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            return None

        if 'postal' in event.lower():
            postcode = values.get(event.upper())
            new_address = address_postcode_click(postcode=postcode, client=client)
            if new_address:
                # update_gui_from_address(address=new_address)
                update_gui_from_address(address=new_address, window=window)

        if 'company_name' in event.lower():
            # copy customer name into address company name field
            company_name_click(address=address, customer=shipment.customer, values=values)
            update_gui_from_address(address=address, window=window)

        if event == '-SUBMIT-':
            update_address_from_gui(values=values, address=address)
            update_contact_from_gui(values=values, contact=contact)
            window.close()
            return address

def address_postcode_click(postcode: str, client, address_popup=address_from_postcode_popup) -> Address | None:
    """ calls address chooser for user to select an address from those existing at either provided or shipment postcode """
    while True:
        try:
            candidates = client.get_address_keys_by_postcode(postcode)
            new_address = address_popup(candidate_keys=candidates, client=client)
        except Exception as e:
            postcode = sg.popup_get_text("Enter Postcode (empty to cancel)")
            if not postcode:
                return None
        else:
            return new_address
