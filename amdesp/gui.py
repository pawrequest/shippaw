import json
import os
from datetime import datetime
from pprint import pprint

import PySimpleGUI as sg

from amdesp.gui_layouts import GuiLayout
from amdesp.utils_pss.utils_pss import Utility


class Gui:
    def __init__(self, app):
        self.client = app.client
        self.config = app.config
        self.shipment = app.shipment
        self.app = app

        self.layouts = GuiLayout(self)

    def gui_ship(self, mode, theme=None):

        match mode:
            case 'out':
                self.shipment.is_return = False
            case 'in':
                self.shipment.is_return = True
            case _:
                sg.popup_error("WRONG MODE")

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
                self.shipment.shipment_request = self.make_request()

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
                    shipment_request = self.make_request()
                    answer = sg.popup_scrolled(f"{decision}?\n{shipment_request}", size=(30, 30))

                    if answer == 'OK':
                        if not self.app.sandbox:
                            if not sg.popup("NOT SANDBOX DO YOU WANT TO PAY?!!!") == 'Yes':
                                continue
                        shipment_id = self.queue_shipment(shipment_request)
                        if 'book' in decision:
                            shipment_return = self.book_collection(shipment_id)
                            sg.popup(f"Collection for {self.shipment.shipment_name} booked")
                        if 'print' in decision:
                            self.print_label()
                        if 'email' in decision:
                            ...
                        self.update_commence()
                        self.log_shipment()
                        break

        window.close()

    def populate_window(self):
        window = self.window
        sender, recipient = self.app.get_sender_recip(self.shipment)
        for field in self.config.address_fields:
            try:
                window[f'-SENDER_{field.upper()}-'].update(getattr(sender.sender_address, field))
                window[f'-RECIPIENT_{field.upper()}-'].update(getattr(recipient.recipient_address, field))
            except Exception as e:
                print(e.__repr__())

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

    def make_request(self):
        values, shipment, client = self.values, self.shipment, self.client
        shipment.parcels = self.layouts.get_parcels(values['-BOXES-'])
        shipment.date = self.layouts.date_menu_map.get(values['-DATE-'])
        shipment.service = self.layouts.service_menu_map.get(values['-SERVICE-'])

        shipment_request = client.shipment_request(
            service_id=shipment.service.service_id,
            parcels=shipment.parcels,
            client_reference=shipment.contact,
            collection_date=shipment.date,
            sender_address=shipment.sender,
            recipient_address=shipment.recipient,
            follow_shipment=True
        )
        return shipment_request

    def get_address_candidates(self, postcode=None):
        shipment, client = self.shipment, self.client
        if postcode is None:
            postcode = shipment.postcode

        while True:
            try:
                candidates = client.get_address_keys_by_postcode(postcode)
            except:
                if sg.popup_yes_no("Bad Postcode - Try again?") == 'Yes':
                    postcode = sg.popup_get_text("Enter Postcode")
                    continue
                else:
                    # no retry = no candidates
                    return None
            else:
                return candidates

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

    def queue_shipment(self, shipment_request):
        shipment = self.shipment
        client = self.client
        if shipment.is_return:
            shipment.inbound_id = client.add_shipment(shipment_request)
            shipment_id = shipment.inbound_id
        else:
            shipment.outbound_id = client.add_shipment(shipment_request)
            shipment_id = shipment.outbound_id
        return shipment_id

    def book_collection(self, shipment_id):
        shipment = self.shipment
        client = self.client
        try:
            shipment_return = client.book_shipments(shipment_id)[0]  # debug there could be more than one here??
            sg.popup_scrolled(f'Shipment booked: \n{shipment_return}', size=(30, 30))
            shipment.collection_booked = True
        except:
            sg.popup_error("Unable to Book")
            return None
        else:
            # save label
            try:
                label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
                label_string = shipment.shipment_name.replace(r'/', '-') + '.pdf'
                shipment.label_location = self.config.label_path / label_string
                label_pdf.download(shipment.label_location)
            except:
                sg.popup_error("Label not downloaded")
            shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
            return shipment_return

    def print_label(self):
        try:
            os.startfile(str(self.shipment.label_location), "print")
        except Exception as e:
            sg.popup_error(f"\n ERROR: Unable to print \n{e}")
        else:
            self.printed = True

    def update_commence(self):
        """
                runs cmclibnet via powershell script to add tracking numbes to commence db

                :return:
                """

        class CommenceEditError(Exception):
            pass

        ps_script = str(self.config.paths['cmc_log'])
        try:  # utility class static method runs powershell script bypassing execuction policy
            ship_id_to_pass = str(
                self.shipment.inbound_id if self.shipment.is_return else self.shipment.outbound_id)
            commence_edit = Utility.powershell_runner(ps_script, self.shipment.category, self.shipment.shipment_name,
                                                      ship_id_to_pass,
                                                      str(self.shipment.is_return), 'debug')

            if commence_edit == 1:
                raise CommenceEditError("\nERROR: Commence Tracking not updated - is Commence running?")

        except CommenceEditError as e:
            ...
            # sg.popup_error(f"{e}")

        except FileNotFoundError as e:
            ...
            # sg.popup(f"ERROR: Unable to log tracking to Commence - FileNotFoundError : {e.filename}")

        except Exception as e:
            ...
            # sg.popup(f"{e=} \nERROR: Unable to log tracking to Commence")

        else:
            ...
            # sg.popup("\nCommence Tracking updated")

    def log_shipment(self):
        # export from object attrs
        shipment = self.shipment
        shipment.boxes = len(self.shipment.parcels)
        export_dict = {}

        for field in self.config.export_fields:
            try:
                if field == 'sender':
                    val = shipment.sender.__repr__()
                    # val = shipment.sender.sender_address
                    # val = f'{val.street} - {val.postal_code}'
                elif field == 'recipient':
                    val = shipment.recipient.__repr__()
                    # val = f'{val.street} - {val.postal_code}'
                    # val = shipment.recipient.recipient_address
                    # val = f'{val.street} - {val.postal_code}'
                else:
                    val = getattr(self.shipment, field)
                    if isinstance(val, datetime):
                        val = f"{val.isoformat(sep=' ', timespec='seconds')}"

                export_dict.update({field: val})
            except Exception as e:
                print(f"{field} not found in shipment \n{e}")

        with open(self.config.paths['log'], 'a') as f:
            json.dump(export_dict, f, sort_keys=True)
            f.write(",\n")
        sg.popup(f" Json exported to {self.config.paths['log']}:\n {export_dict}")

    def email_label(self):
        ...
