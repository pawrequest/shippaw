import inspect
import json
import os
import xml.etree.ElementTree as ET
from pprint import pprint

import PySimpleGUI
from dbfread import DBF

import PySimpleGUI as sg
from datetime import datetime
from dateutil.parser import parse

# from AmDesp.Shipment import Shipment2
# from AmDesp.config import Config, print_and_pop
# from AmDesp.gui import Gui
from AmDesp import shipment, config, gui, gui_layouts

import dotenv

from AmDesp.utils_pss.utils_pss import Utility

dotenv.load_dotenv()

DEBUG = False

LINE = f"{'-' * 130}"
TABBER = "\t\t"


# SANDBOX_SHIPMENT_ID = '100786-5633'
# SHIPMENT_ID = '100786-20850029'


class App:
    def __init__(self, sandbox=False):  # creat app-obj
        # create config object
        self.config = config.Config()
        self.sandbox = sandbox
        try:
            self.client = self.config.get_client(sandbox=sandbox)
        except Exception as e:
            print_and_pop(f"Unable to fetch DespatchBay Client due to: \n{e}")

        # todo genericise
        #

    def run(self, mode, in_file:str):
        self.mode = mode
        self.shipments = []
        file_ext = in_file.split('.')[-1]
        active_gui = gui.Gui(self)

        match file_ext:
            case 'xml':
                ship_dict = self.ship_dict_from_xml(in_file)
                self.shipments.append(shipment.Shipment(app=self, ship_dict=ship_dict))
            # case 'dbase':
            #     for record in
            #     ship_dict =
        for shipment in self.shipments:
            ...

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



    def get_address_candidates(self, shipment, postcode=None):
        client = self.client
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

        # elif 'bulk' in mode:
        #     self.bulk = self.get_bulk_dbase()
        #     for shipment in self.bulk:
        #         self.shipments.append(shipment)
        #     gui = Gui(self)
        #     self.gui = gui
        #
        #     match mode:
        #         case 'ship_out':
        #             gui.gui_ship('out')
        #             sg.popup("COMPLETE")
        #         case 'ship_in':
        #             gui.gui_ship('in')
        #             sg.popup("COMPLETE")
        #         case 'track_out':
        #             try:
        #                 gui.layouts.tracking_viewer_window(self.shipment.outbound_id)
        #             except:
        #                 sg.popup_error("No Shipment ID")
        #         case 'track_in':
        #             try:
        #                 gui.layouts.tracking_viewer_window(self.shipment.inbound_id)
        #             except:
        #                 sg.popup_error("No Shipment ID")

    def ship_dict_from_xml(self, xml_file):
        # inspect xml
        config = self.config
        shipment_fields = config.shipment_fields
        ship_dict = dict()
        tree = ET.parse(xml_file)
        root = tree.getroot()
        fields = root[0][2]

        category = root[0][0].text
        for field in fields:
            k = field[0].text
            k = to_snake_case(k)
            v = field[1].text
            if v:
                k = unsanitise(k)
                v = unsanitise(v)

                if "Number" in k:
                    v = v.replace(',', '')
                if k == 'name':
                    k = 'shipment_name'
                # if pattern.search(k):
                if k[:6] == "deliv ":
                    k = k.replace('deliv', 'delivery')
                k = k.replace('delivery_', '')
                if k == 'tel':
                    k = 'telephone'
                if k == 'all_address':
                    k = 'address_as_str'
                ship_dict.update({k: v})

        # get customer name
        if category == "Hire":
            ship_dict['customer'] = root[0][3].text
        elif category == "Customer":
            ship_dict['customer'] = fields[0][1].text
            ship_dict[
                'shipment_name'] = f'{ship_dict["shipment_name"]} - {datetime.now().isoformat(" ", timespec="seconds")}'
        elif category == "Sale":
            ship_dict['customer'] = root[0][3].text

        # convert to date object
        ship_dict['send_out_date'] = ship_dict.get('send_out_date', None)
        if ship_dict['send_out_date']:
            ship_dict['send_out_date'] = parse(ship_dict['send_out_date'])
        else:
            ship_dict['send_out_date'] = datetime.today()

        ship_dict['category'] = category
        ship_dict['search_term'] = parse_amherst_address_string(ship_dict['address'])

        ship_dict['boxes'] = ship_dict.get('boxes', 1)

        missing = []
        for attr_name in shipment_fields:
            if attr_name not in ship_dict.keys():
                if attr_name not in ['cost', 'inbound_id', 'outbound_id']:
                    missing.append(attr_name)
        if missing:
            print_and_pop(f"*** Warning - {missing} not found in ship_dict - Warning ***")
        return ship_dict

    # def get_bulk_dbase(self):
    #     datapath = self.config.paths['dbase_import']
    #     try:
    #         bulk_dbase = DBF(datapath)
    #         dbase_records = []
    #         for single_record in (bulk_dbase.records):
    #             obj = Shipment(self, single_record)
    #             dbase_records.append(obj)
    #     except Exception as e:
    #         print_and_pop(e.__repr__())
    #     else:
    #         return dbase_records

    def get_sender_recip(self):
        shipment = self.shipment
        client = self.client

        # shipment is a return so recipient is homebase
        if shipment.is_return:
            recipient = shipment.home_recipient
            try:
                sender_address = client.find_address(shipment.postcode, shipment.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                sender_address = self.gui.address_chooser(candidates)
            sender = client.sender(name=shipment.name, email=shipment.email,
                                   telephone=shipment.telephone, sender_address=sender_address)

        # not a return so we are sender
        if not shipment.is_return:
            sender = shipment.home_sender
            try:
                recipient_address = client.find_address(shipment.postcode, shipment.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                recipient_address = self.gui.address_chooser(candidates)
            recipient = client.recipient(name=shipment.name, email=shipment.email,
                                         telephone=shipment.telephone, recipient_address=recipient_address)

            shipment.sender, shipment.recipient = sender, recipient

        return sender, recipient


def to_snake_case(input_string):
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string


def parse_amherst_address_string(str_address):
    firstline = str_address.strip().split("\n")[0]
    first_block = (str_address.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    for char in firstline:
        if not char.isalnum() and char != " ":
            firstline = firstline.replace(char, "")

    if first_char.isnumeric():
        return first_block
    else:
        return firstline


def unsanitise(input_string):
    """ deals with special and escape chars"""
    input_string = input_string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;",
                                                                                             chr(39)).replace(
        "&lt;",
        chr(60)).replace(
        "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    return input_string


def debug_msg(e=None):
    debug_msg = "\n\n"
    debug_msg += f"\nCurrent method = {inspect.currentframe().f_back.f_code.co_name}\n"
    if e:
        debug_msg += f"ERROR: {e}" if {e} else None


def print_and_pop(print_text: str):
    sg.popup(print_text)
    print(print_text)


def print_and_long_pop(print_string: str):
    sg.popup_scrolled(print_string)
    pprint(print_string)


def log_shipment(config, shipment):
    # export from object attrs
    shipment = shipment
    shipment.boxes = len(shipment.parcels)
    export_dict = {}

    for field in config.export_fields:
        try:
            if field == 'sender':
                val = shipment.sender.sender_address
                val = f'{val.street} - {val.postal_code}'
            elif field == 'recipient':
                val = shipment.recipient.recipient_address
                val = f'{val.street} - {val.postal_code}'
            else:
                val = getattr(shipment, field)
                if isinstance(val, datetime):
                    val = f"{val.isoformat(sep=' ', timespec='seconds')}"

            export_dict.update({field: val})
        except Exception as e:
            print(f"{field} not found in shipment \n{e}")

    with open(config.paths['log'], 'a') as f:
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")
    sg.popup(f" Json exported to {config.paths['log']}:\n {export_dict}")


def update_commence(config, shipment):
    """
            runs cmclibnet via powershell script to add tracking numbes to commence db

            :return:
            """

    class CommenceEditError(Exception):
        pass

    ps_script = str(config.paths['cmc_log'])
    try:  # utility class static method runs powershell script bypassing execuction policy
        ship_id_to_pass = str(
            shipment.inbound_id if shipment.is_return else shipment.outbound_id)
        commence_edit = Utility.powershell_runner(ps_script, shipment.category, shipment.shipment_name,
                                                  ship_id_to_pass,
                                                  str(shipment.is_return), 'debug')

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


def print_label(shipment):
    try:
        os.startfile(str(shipment.label_location), "print")
    except Exception as e:
        sg.popup_error(f"\n ERROR: Unable to print \n{e}")
    else:
        shipment.printed = True


def book_collection(client1, config, shipment):
    client = client1
    try:# todo could there be multiple ship_ids?
        shipment_return = client.book_shipments(shipment.shipment_id)[0]
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
            shipment.label_location = config.label_path / label_string
            label_pdf.download(shipment.label_location)
        except:
            sg.popup_error("Label not downloaded")
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        return shipment_return


def queue_shipment(client1, shipment):
    client = client1
    if shipment.is_return:
        shipment.inbound_id = client.add_shipment(shipment.shipment_request)
        shipment_id = shipment.inbound_id
    else:
        shipment.outbound_id = client.add_shipment(shipment.shipment_request)
        shipment_id = shipment.outbound_id
    return shipment_id


def make_request(values1, client1, layouts, shipment):
    values, client = values1, client1
    shipment.parcels = layouts.get_parcels(values['-BOXES-'])
    shipment.date = layouts.date_menu_map.get(values['-DATE-'])
    shipment.service = layouts.service_menu_map.get(values['-SERVICE-'])

    shipment_request = client.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=shipment.name,
        collection_date=shipment.date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )
    return shipment_request