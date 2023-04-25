# event, values = sg.Window('Window Title', [[sg.Text('Enter Something')], [sg.Input(key='-IN-'),],[sg.Button('OK'), sg.Button('Cancel')]]).read(close=True)

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address
from despatchbay.despatchbay_sdk import DespatchBaySDK

from amdesp_shipper.config import Config
from amdesp_shipper.enums import Contact, FieldsList
from amdesp_shipper.main_gui import Gui
from amdesp_shipper.gui_params import address_fieldname_params, address_input_params
from amdesp_shipper.shipment import Shipment


class AddressGui(Gui):
    def __init__(self, config: Config, client: DespatchBaySDK, shipment: Shipment, contact: Contact, address: Address):
        super().__init__(config, client)
        self.contact = contact
        self.address = address
        self.shipment = shipment
        self.window = self.get_contact_window()

    def address_gui_loop(self) -> Address:
        """ Gui loop, takes an address and shipment for contact details,
        allows editing / replacing before returning address"""
        client = self.client
        # contact = shipment.get_sender_or_recip()

        while True:
            self.event, self.values = self.window.read()
            if self.event in (sg.WINDOW_CLOSED, '-SUBMIT-', 'Exit'):
                address = self.update_address_from_gui()
                self.window.close()
                return address

            if 'postal' in self.event.lower():
                postcode = self.values.get(self.event.upper())
                new_address = self.address_postcode_click(client=client, postcode=postcode)
                if new_address:
                    self.update_gui_from_address(address=new_address)

            if 'company_name' in self.event.lower():
                # copy customer name into address comany name field
                address = self.company_name_click()
                self.update_gui_from_address(address=address)

            # if 'submit' in self.event.lower():
            #     address = self.update_address_from_gui()
            #     self.window.close()
            #     return address

    def company_name_click(self):
        address = self.update_address_from_gui()
        setattr(address, 'company_name', self.shipment.customer)
        # window[event.upper()].update(shipment.customer)
        return address

    def address_postcode_click(self, client: DespatchBaySDK, postcode: str) -> Address|None:

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

    def get_contact_window(self):
        contact = self.contact
        address = self.address
        layout = [
            [sg.Text(f'Name:', **address_fieldname_params),
             sg.InputText(f'{contact.name}', key=f'-NAME-', **address_input_params)],

            [sg.Text(f'Email:', **address_fieldname_params),
             sg.InputText(f'{contact.email}', key=f'-EMAIL-', **address_input_params)],

            [sg.Text(f'Telephone:', **address_fieldname_params),
             sg.InputText(f'{contact.telephone}', key=f'-TELEPHONE-', **address_input_params)],

            [self.get_address_frame(address=address)],

            [sg.B('Submit', k=f'-SUBMIT-')]
        ]
        return sg.Window('Address', layout=layout)

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
        return self.address

    def get_address_frame(self, address: Address, index: str = None) -> sg.Frame:
        layout = []
        params = address_fieldname_params.copy()
        input_text = ''
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
                label_text = sg.B(key_for_humans, k=key.lower(), **params)
            else:
                label_text = sg.Text(key_for_humans, k=key.lower(), **address_fieldname_params)

            input_box = sg.InputText(input_text, k=key.upper(), **address_input_params)
            layout.append([label_text, input_box])

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
