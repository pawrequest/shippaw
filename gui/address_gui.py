import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address
from despatchbay.despatchbay_sdk import DespatchBaySDK

from core.enums import Contact, FieldsList
from gui.gui_params import address_fieldname_params, address_input_params
from gui.main_gui import Gui
from shipper.shipment import Shipment


class AddressGui(Gui):
    def __init__(self, client: DespatchBaySDK, shipment: Shipment,
                 contact: Contact | None, address: Address | None):
        super().__init__()
        self.contact = contact
        self.address = address
        self.shipment = shipment
        # self.window = self.get_contact_window()
        self.window = self.get_comparison_address_window()
        self.client = client

    def get_address(self):
        """ Gui loop, takes an address and shipment for contact details,
        allows editing / replacing address and contact """
        client = self.client
        # contact = shipment.get_sender_or_recip()

        while True:
            self.event, self.values = self.window.read()
            if self.event == sg.WINDOW_CLOSED:
                return None

            if 'postal' in self.event.lower():
                postcode = self.values.get(self.event.upper())
                new_address = self.address_postcode_click(client=client, postcode=postcode)
                if new_address:
                    self.update_gui_from_address(address=new_address)

            if 'company_name' in self.event.lower():
                # copy customer name into address comany name field
                self.company_name_click()
                self.update_gui_from_address(address=self.address)

            if 'submit' in self.event.lower():
                self.update_address_from_gui()
                self.update_contact_from_gui()
                self.window.close()
                return self.address

    def company_name_click(self):
        self.update_address_from_gui()
        setattr(self.address, 'company_name', self.shipment.customer)

    def address_postcode_click(self, client: DespatchBaySDK, postcode: str) -> Address | None:

        """ calls address chooser for user to select an address from those existing at either provided or shipment postcode """
        while True:
            try:
                candidates = client.get_address_keys_by_postcode(postcode)
                candidate_key_dict = {candidate.address: candidate.key for candidate in candidates}
                new_address = self.address_chooser_popup(candidate_dict=candidate_key_dict, client=client)
            except Exception as e:
                postcode = sg.popup_get_text("Enter Postcode (empty to cancel)")
                if not postcode:
                    return None
            else:
                return new_address

    def commence_address_frame(self):
        commence_text = f'{self.shipment.customer} \n{self.shipment._address_as_str}'
        return sg.Frame(title='Address Details From Commence:', layout=[
            [sg.Text(commence_text)]
        ])

    def get_comparison_address_window(self):
        commence_frame = self.commence_address_frame()
        address_col = sg.Col(layout=[
            [self.get_contact_frame()],
            [self.get_address_frame(address=self.address)]
        ])

        return sg.Window('Manual Address Selector', layout=[[commence_frame, address_col]])

    def get_modular_address_window(self):
        layout = [
            [self.get_contact_frame()],
            [self.get_address_frame(address=self.address)],
        ]
        return sg.Window('Address and Contact Details', layout=layout)

    def get_contact_window(self):
        layout = [
            [sg.Text(f'Name:', **address_fieldname_params),
             sg.InputText(f'{self.contact.name}', key=f'-NAME-', **address_input_params)],

            [sg.Text(f'Email:', **address_fieldname_params),
             sg.InputText(f'{self.contact.email}', key=f'-EMAIL-', **address_input_params)],

            [sg.Text(f'Telephone:', **address_fieldname_params),
             sg.InputText(f'{self.contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],

            [self.get_address_frame(address=self.address)],

            [sg.B('Submit', k=f'-SUBMIT-')]
        ]
        return sg.Window('Address', layout=layout)

    def get_contact_frame(self):
        layout = [
            [sg.Text(f'Name:', **address_fieldname_params),
             sg.InputText(f'{self.contact.name}', key=f'-NAME-', **address_input_params)],

            [sg.Text(f'Email:', **address_fieldname_params),
             sg.InputText(f'{self.contact.email}', key=f'-EMAIL-', **address_input_params)],

            [sg.Text(f'Telephone:', **address_fieldname_params),
             sg.InputText(f'{self.contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],
        ]
        return sg.Frame("Contact Details", layout=layout)

    def update_gui_from_address(self, address: Address):
        if address:
            address_dict = {k: v for k, v in vars(address).items() if 'soap' not in k}
            address_dict.pop('country_code', None)
            for k, v in address_dict.items():
                self.window[f'-ADDRESS_{k.upper()}-'].update(v or '')

    def update_address_from_gui(self):
        for field in FieldsList.address.value:
            value = self.values.get(f'-ADDRESS_{field.upper()}-', None)
            setattr(self.address, field, value)

    def update_contact_from_gui(self):
        for field in FieldsList.contact.value:
            value = self.values.get(f'-{field.upper()}-', None)
            setattr(self.contact, field, value)

    def get_address_frame(self, address: Address, index: str = None) -> sg.Frame:
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

    def address_chooser_popup(self, candidate_dict: dict, client: DespatchBaySDK) -> Address:
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

    # def get_contact_frame(self, config: Config, contact: Contact, address: Address):
    #     layout = [
    #         [sg.Text(f'Name:', **address_fieldname_params),
    #          sg.InputText(f'{contact.name}', key=f'-NAME-', **address_input_params)],
    #
    #         [sg.Text(f'Email:', **address_fieldname_params),
    #          sg.InputText(f'{contact.email}', key=f'-EMAIL-', **address_input_params)],
    #
    #         [sg.Text(f'Telephone:', **address_fieldname_params),
    #          sg.InputText(f'{contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],
    #
    #         [get_address_frame(address=address, address_fields=config.fields.address)],
    #
    #         [sg.B('Submit', k=f'-SUBMIT-')]
    #     ]
    #     return sg.Frame('Contact Frame', layout=layout)
