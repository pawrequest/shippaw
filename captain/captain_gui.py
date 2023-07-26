import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address
from despatchbay.despatchbay_sdk import DespatchBaySDK

from core.enums import Contact, FieldsList
from gui.gui_params import address_fieldname_params, address_input_params
from gui.main_gui import Gui
from shipper.shipment import Shipment


def get_address(client, window):
    """ Gui loop, takes an address and shipment for contact details,
    allows editing / replacing address and contact """

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            return None

        if 'postal' in event.lower():
            postcode = values.get(event)
            new_address = address_postcode_click(client=client, postcode=postcode)
            if new_address:
                update_gui_from_address(address=new_address)

        if 'company_name' in event.lower():
            # copy customer name into address comany name field
            company_name_click()
            update_gui_from_address(address=address)

        if 'submit' in event.lower():
            update_address_from_gui()
            update_contact_from_gui()
            window.close()
            return address

def company_name_click():
    update_address_from_gui()
    setattr(address, 'company_name', shipment.customer)

def address_postcode_click(client: DespatchBaySDK, postcode: str) -> Address | None:

    """ calls address chooser for user to select an address from those existing at either provided or shipment postcode """
    while True:
        try:
            candidates = client.get_address_keys_by_postcode(postcode)
            candidate_key_dict = {candidate.address: candidate.key for candidate in candidates}
            new_address = address_chooser_popup(candidate_dict=candidate_key_dict, client=client)
        except Exception as e:
            postcode = sg.popup_get_text("Enter Postcode (empty to cancel)")
            if not postcode:
                return None
        else:
            return new_address

def commence_address_frame():
    commence_text = f'{shipment.customer} \n{shipment._address_as_str}'
    return sg.Frame(title='Address Details From Commence:', layout=[
        [sg.Text(commence_text)]
    ])

def get_comparison_address_window():
    commence_frame = commence_address_frame()
    address_col = sg.Col(layout=[
        [get_contact_frame()],
        [get_address_frame(address=address)]
    ])

    return sg.Window('Manual Address Selector', layout=[[commence_frame, address_col]])

def get_modular_address_window():
    layout = [
        [get_contact_frame()],
        [get_address_frame(address=address)],
    ]
    return sg.Window('Address and Contact Details', layout=layout)

def get_contact_window():
    layout = [
        [sg.Text(f'Name:', **address_fieldname_params),
         sg.InputText(f'{contact.name}', key=f'-NAME-', **address_input_params)],

        [sg.Text(f'Email:', **address_fieldname_params),
         sg.InputText(f'{contact.email}', key=f'-EMAIL-', **address_input_params)],

        [sg.Text(f'Telephone:', **address_fieldname_params),
         sg.InputText(f'{contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],

        [get_address_frame(address=address)],

        [sg.B('Submit', k=f'-SUBMIT-')]
    ]
    return sg.Window('Address', layout=layout)

def get_contact_frame():
    layout = [
        [sg.Text(f'Name:', **address_fieldname_params),
         sg.InputText(f'{contact.name}', key=f'-NAME-', **address_input_params)],

        [sg.Text(f'Email:', **address_fieldname_params),
         sg.InputText(f'{contact.email}', key=f'-EMAIL-', **address_input_params)],

        [sg.Text(f'Telephone:', **address_fieldname_params),
         sg.InputText(f'{contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],
    ]
    return sg.Frame("Contact Details", layout=layout)

def update_gui_from_address(address: Address):
    if address:
        address_dict = {k: v for k, v in vars(address).items() if 'soap' not in k}
        address_dict.pop('country_code', None)
        for k, v in address_dict.items():
            window[f'-ADDRESS_{k.upper()}-'].update(v or '')

def update_address_from_gui():
    for field in FieldsList.address.value:
        value = values.get(f'-ADDRESS_{field.upper()}-', None)
        setattr(address, field, value)

def update_contact_from_gui():
    for field in FieldsList.contact.value:
        value = values.get(f'-{field.upper()}-', None)
        setattr(contact, field, value)

def get_address_frame(address: Address, index: str = None) -> sg.Frame:
    layout = []
    params = address_fieldname_params.copy()

    for field in FieldsList.address.value:
        if index:
            key = f'-{index}_ADDRESS_{field}-'.upper()
        else:
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

def address_chooser_popup(candidate_dict: dict, client: DespatchBaySDK) -> Address:
    """ popup mapping address keys to human readable addresses
    """
    default_value = next(c for c in candidate_dict)

    layout = [[sg.Listbox(list(candidate_dict.keys()), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, expand_x=True,
                          expand_y=True, enable_events=True, size=(50, 20), bind_return_key=True,
                          default_values=default_value, k='select', auto_size_text=True)]]

    window = sg.Window('Address Selector', layout)
    event, values = window.read()
    window.close()

    if event == 'select':
        address_key = candidate_dict.get(values['select'][0])
        address = client.get_address_by_key(address_key)
        window.close()
        return address
