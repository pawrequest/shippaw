from pprint import pprint

import PySimpleGUI as sg

from AmDesp.gui_layouts import GuiLayout
from AmDesp.shipper import log_shipment, update_commence, print_label, book_collection, queue_shipment, make_request


class Gui:
    def __init__(self, app):
        self.client = app.client
        self.config = app.config
        # self.shipment = app.shipment
        self.app = app

        self.layouts = GuiLayout(self)

    def gui_ship(self, shipment, theme=None):

        window = self.layouts.main_window()
        self.window = window
        self.populate_window()

        if self.app.sandbox:
            self.theme = sg.theme('Tan')
        else:
            sg.theme('Dark Blue')
        if theme:
            sg.theme(theme)

        while True:
            if not window:
                break
            event, values = window.read()
            window['-SENDER_POSTAL_CODE-'].bind("<Return>", "_Enter")
            window['-RECIPIENT_POSTAL_CODE-'].bind("<Return>", "_Enter")

            self.event, self.values = event, values
            shipment = self.shipment
            pprint(f'{event}  -  {[values.items()]}')
            if not self.shipment.shipment_request:
                self.shipment.shipment_request = make_request(self.values, self.client, self.layouts)

            if event in (sg.WINDOW_CLOSED, 'Exit'):
                break

            elif event == "Set Theme":
                print("[LOG] Clicked Set Theme!")
                theme_chosen = values['-THEME LISTBOX-'][0]
                print("[LOG] User Chose Theme: " + str(theme_chosen))
                window.close()
                self.gui_ship(mode='out', theme=theme_chosen)

            if event == '-DATE-':
                window['-DATE-'].update({'background_color': 'red'})

            # click company name to copy customer in
            if 'company_name' in event:
                window[event.upper()].update(self.shipment.customer)
                # window[event.upper()].refresh()

            # click 'postcode' or Return in postcode box to get address to choose from and update shipment
            if 'postal_code' in event.lower():
                self.new_address_from_postcode()

            if event == '-INBOUND_ID-':
                self.layouts.tracking_viewer_window(shipment.inbound_id)
            if event == '-OUTBOUND_ID-':
                self.layouts.tracking_viewer_window(shipment.outbound_id)

            if event == '-GO-':
                decision = values['-QUEUE OR BOOK-'].lower()
                if 'queue' or 'book' in decision:
                    shipment_request = make_request(self.values, self.client, self.layouts)
                    answer = sg.popup_scrolled(f"{decision}?\n{shipment_request}", size=(30, 30))

                    if answer == 'OK':
                        if not self.app.sandbox:
                            if not sg.popup("NOT SANDBOX DO YOU WANT TO PAY?!!!") == 'Yes':
                                continue
                        shipment_id = queue_shipment(self.client, shipment_request)
                        if 'book' in decision:
                            shipment_return = book_collection(self.client, self.config, shipment_id)
                            sg.popup(f"Collection for {self.shipment.shipment_name} booked")
                        if 'print' in decision:
                            print_label()
                        if 'email' in decision:
                            ...
                        update_commence(self.config)
                        log_shipment(self.config)
                        break

        window.close()

    def populate_window(self, shipment):
        window = self.window
        sender, recipient = shipment.get_sender_recip()
        for field in self.config.address_fields:
            try:
                window[f'-SENDER_{field.upper()}-'].update(getattr(sender.sender_address.sender_address, field))
                window[f'-RECIPIENT_{field.upper()}-'].update(getattr(recipient.recipient_address, field))
            except Exception as e:
                ...

        adict = {'sender': sender, 'recipient': recipient}

        for name, obj in adict.items():
            for field in self.config.contact_fields:
                value = getattr(obj, field, None)
                if value is None:
                    value = sg.popup_get_text(f"{field} Missing from {name} record- please enter:")
                    setattr(obj, field, value)
                window[f'-{name.upper()}_{field.upper()}-'].update(value)

    def new_address_from_postcode(self):
        """ click 'postcode' label, or press Return in postcode input to call.
            parses sender vs recipient from event code.
            takes postcode from window, gets list of candidate addresses with given postcode
            popup a chooser,
            """
        event, values, shipment, window = self.event, self.values, self.shipment, self.window
        postcode = None
        mode = None
        if 'sender' in event.lower():
            mode = 'sender'
            postcode = values['-SENDER_POSTAL_CODE-']
        elif 'recipient' in event.lower():
            mode = 'recipient'
            postcode = values['-RECIPIENT_POSTAL_CODE-']

        address_dict={}
        try:
            candidates = self.get_address_candidates(postcode=postcode)
            chosen_address = self.address_chooser(candidates)
            address_dict = {k: v for k, v in vars(chosen_address).items() if 'soap' not in k}
            address_dict.pop('country_code', None)

            if mode == 'sender':
                shipment.sender.sender_address = chosen_address
            elif mode == 'recipient':
                shipment.recipient.recipient_address = chosen_address

            for k, v in address_dict.items():
                window[f'-{mode.upper()}_{k.upper()}-'].update(v if v else '')
        except:
            pass

    # def get_address_candidates(self, postcode=None):
    #     shipment, client = self.shipment, self.client
    #     if postcode is None:
    #         postcode = shipment.postcode
    #
    #     while True:
    #         try:
    #             candidates = client.get_address_keys_by_postcode(postcode)
    #         except:
    #             if sg.popup_yes_no("Bad Postcode - Try again?") == 'Yes':
    #                 postcode = sg.popup_get_text("Enter Postcode")
    #                 continue
    #             else:
    #                 # no retry = no candidates
    #                 return None
    #         else:
    #             return candidates

    def address_chooser(self, candidates):
        client = self.client
        # build address option menu dict
        address_key_dict = {}
        for candidate in candidates:
            candidate_hr = candidate.address
            address_key_dict.update({candidate_hr: candidate.key})

        # deploy address option popup using dict as mapping
        address_key = self.layouts.combo_popup(address_key_dict)
        if address_key:
            address = client.get_address_by_key(address_key)
            return address

    def email_label(self):
        ...
