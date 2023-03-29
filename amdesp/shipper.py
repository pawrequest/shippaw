import json
import os
import pathlib
import xml.etree.ElementTree as ET
from datetime import datetime
from pprint import pprint

import PySimpleGUI as sg
import dotenv
from PySimpleGUI import Window
from dateutil.parser import parse
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.despatchbay.despatchbay_entities import ShipmentRequest

from amdesp.gui_layouts import GuiLayout, tracking_viewer_window, combo_popup
from amdesp.utils_pss.utils_pss import Utility, unsanitise
from amdesp.config import Config

DEBUG = False
dotenv.load_dotenv()
LINE = f"{'-' * 130}"
TABBER = "\t\t"


class App:
    def __init__(self):
        self.printed = None
        self.theme = None
        self.service_menu_map = {}
        self.date_menu_map = {}
        self.shipments = []

    def get_service_menu(self, shipment, config, client):
        services = client.get_services()
        services_menu_map = {}
        menu_def = []

        # get services
        chosen_service = None
        chosen_service_hr = None
        for potential_service in services:
            if potential_service.service_id == config.service_id:
                chosen_service = potential_service
                chosen_service_hr = chosen_service.name
            menu_def.append(potential_service.name)
            services_menu_map.update({potential_service.name: potential_service})
        if not chosen_service:
            sg.popup("Default service unavailable")
            chosen_service = services[0]
            chosen_service_hr = chosen_service.name

        shipment.service = chosen_service
        self.service_menu_map = services_menu_map

        return {'values': menu_def, 'default_value': chosen_service_hr}

    def get_dates_menu(self, shipment, client, config):
        dates_params = {}
        # send-out date as datetime obj
        send_date = shipment.date
        # potential dates as dbay date objs
        available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.courier_id)
        datetime_mask = config.datetime_masks['DT_DISPLAY']
        menu_def = []
        chosen_date_db = None
        chosen_date_hr = None

        for potential_collection_date in available_dates:
            potential_date = parse(potential_collection_date.date)
            potential_date_hr = datetime.strftime(potential_date.date(), datetime_mask)

            if potential_date == send_date:
                potential_date_hr = potential_date_hr
                chosen_date_db = potential_collection_date
                chosen_date_hr = potential_date_hr
                dates_params.update({'background_color': 'green'})
            # to use human readable names in button and retrieve object later
            self.date_menu_map[potential_date_hr] = potential_collection_date
            # self.date_menu_map.update(potential_date_hr=potential_collection_date)
            menu_def.append(potential_date_hr)
        if not chosen_date_db:
            dates_params.update({'background_color': 'purple'})
            chosen_date_db = available_dates[0]
            chosen_date_hr = menu_def[0]
            self.date_menu_map[chosen_date_hr] = chosen_date_db

        shipment.date = chosen_date_db
        dates_params.update(default_value=chosen_date_hr, values=menu_def)
        return dates_params

    def make_request(self, values, shipment, client):
        shipment.parcels = get_parcels(values['-BOXES-'], client=client, shipment=shipment)
        shipment.date = self.date_menu_map.get(values['-DATE-'])
        shipment.service = self.service_menu_map.get(values['-SERVICE-'])

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

    def populate_window(self, window, config, shipment, client):
        sender, recipient = get_sender_recip(shipment, client=client)
        services_dict = self.get_service_menu(client=client, config=config, shipment=shipment)
        dates_dict = self.get_dates_menu(shipment=shipment, client=client, config=config)
        q_o_b_dict = get_queue_or_book_menu(shipment=shipment)
        for field in config.address_fields:
            try:
                window[f'-SENDER_{field.upper()}-'].update(getattr(sender.sender_address, field))
                window[f'-RECIPIENT_{field.upper()}-'].update(getattr(recipient.recipient_address, field))
            except Exception as e:
                print_and_pop(e.__repr__())
        window['-SHIPMENT_NAME-'].update(shipment.shipment_name)
        # todo color date based on match.... how to update without bg-color in update method?
        window['-DATE-'].update(values=dates_dict['values'], value=dates_dict['default_value'])
        window['-SERVICE-'].update(values=services_dict['values'], value=services_dict['default_value'])
        if shipment.inbound_id:
            window['-INBOUND_ID-'].update(shipment.inbound_id, enable_events=True)
        if shipment.outbound_id:
            window['-OUTBOUND_ID-'].update(shipment.outbound_id, enable_events=True)
        window['-QUEUE_OR_BOOK-'].update(values=q_o_b_dict['values'], value=q_o_b_dict['default_value'])
        window['-BOXES-'].update(value=shipment.boxes or 1)

        adict = {'sender': sender, 'recipient': recipient}
        for name, obj in adict.items():
            for field in config.contact_fields:
                value = getattr(obj, field, None)
                if value is None:
                    value = sg.popup_get_text(f"{field} Missing from {name} record- please enter:")
                    setattr(obj, field, value)
                window[f'-{name.upper()}_{field.upper()}-'].update(value)

    def gui_ship(self, client, config, shipment, sandbox, theme=None):
        window = GuiLayout().main_window()
        self.populate_window(shipment=shipment, config=config, client=client, window=window)

        if sandbox:
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
            pprint(f'{event}  -  {[values.items()]}')
            # if not shipment.shipment_request:
            #     shipment.shipment_request = self.make_request(client=client, shipment=shipment,values=values)
            if event in (sg.WINDOW_CLOSED, 'Exit'):
                break

            elif event == "Set Theme":
                print("[LOG] Clicked Set Theme!")
                theme_chosen = values['-THEME LISTBOX-'][0]
                print("[LOG] User Chose Theme: " + str(theme_chosen))
                window.close()
                self.gui_ship(client=client, config=config, sandbox=sandbox, theme=theme_chosen, shipment=shipment)

            if event == '-DATE-':
                window['-DATE-'].update({'background_color': 'red'})

            # click company name to copy customer in
            if 'company_name' in event:
                window[event.upper()].update(shipment.customer)
                # window[event.upper()].refresh()

            # click 'postcode' or Return in postcode box to get address to choose from and update shipment
            if 'postal_code' in event.lower():
                new_address_from_postcode(client=client, shipment=shipment, event=event, window=window,
                                          values=values)

            if event == '-INBOUND_ID-':
                tracking_viewer_window(shipment.inbound_id, client=client)
            if event == '-OUTBOUND_ID-':
                tracking_viewer_window(shipment.outbound_id, client=client)

            if event == '-GO-':
                decision = values['-QUEUE_OR_BOOK-'].lower()
                if 'queue' or 'book' in decision:
                    shipment_request = self.make_request(shipment=shipment, values=values, client=client)
                    answer = sg.popup_scrolled(f"{decision}?\n{shipment_request}", size=(30, 30))

                    if answer == 'OK':
                        if not sandbox:
                            if not sg.popup("NOT SANDBOX DO YOU WANT TO PAY?!!!") == 'Yes':
                                continue
                        shipment_id = queue_shipment(shipment_request=shipment_request, shipment=shipment,
                                                     client=client)
                        if 'book' in decision:
                            shipment_return = book_collection(shipment_id=shipment_id, shipment=shipment,
                                                              client=client, config=config)
                            sg.popup(f"Collection for {shipment.shipment_name} booked")
                        if 'print' in decision:
                            self.print_label(shipment=shipment)
                        if 'email' in decision:
                            ...
                        update_commence(config=config, shipment=shipment)
                        log_shipment(config=config, shipment=shipment)
                        break

        window.close()

    def print_label(self, shipment):
        try:
            os.startfile(str(shipment.label_location), "print")
        except Exception as e:
            sg.popup_error(f"\n ERROR: Unable to print \n{e}")
        else:
            self.printed = True

    def email_label(self):
        ...


class Shipment:
    def __init__(self, ship_dict, is_return=False):
        """
        :param ship_dict: a dictionary of shipment details
        :param is_return: shipment is outbound or inbound?
        """
        self.category = ship_dict['category']
        self.shipment_name = ship_dict['shipment_name']
        self.date = ship_dict['send_out_date']
        self.address_as_str = ship_dict['address_as_str']
        self.contact = ship_dict['contact']
        self.company_name = None
        self.postcode = ship_dict['postcode']
        self.boxes = ship_dict['boxes']
        self.status = ship_dict['status']
        self.email = ship_dict['email']
        self.telephone = ship_dict['telephone']
        self.customer = ship_dict['customer']
        self.is_return = is_return
        self.inbound_id = ship_dict.get('inbound_id', None)
        self.outbound_id = ship_dict.get('outbound_id', None)
        self.service = None
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = False
        self.search_term = parse_amherst_address_string(self.address_as_str)

        if DEBUG:
            print_and_long_pop(f"\n{self=}\n")


def setup_commence(config: Config()):
    """ looks for CmcLibNet in prog files, if absent attempts to install from path defined in config.toml"""
    try:
        if not config.cmc_dll.exists():
            raise FileNotFoundError("CmcLibNet not installed - launching setup.exe")
    except Exception as e:
        try:
            config.install_cmc_lib_net()
        except Exception as e:
            print_and_pop("Unable to find or install CmcLibNet - logging to commence is impossible")
            # error message built into cmclibnet installer


def get_parcels(num_parcels: int, client: DespatchBaySDK, shipment: Shipment):
    # num_parcels = int(num_parcels.split(" ")[0])
    parcels = []
    for x in range(int(num_parcels)):
        parcel = client.parcel(
            contents="Radios",
            value=500,
            weight=6,
            length=60,
            width=40,
            height=40,
        )
        parcels.append(parcel)
    shipment.parcels = parcels
    return parcels


def get_queue_or_book_menu(shipment:Shipment):
    q_o_b_dict = {}
    print_or_email = "email" if shipment.is_return else "print"
    values = [
        f'Book and {print_or_email}',
        'Book only',
        'Queue only'
    ]
    default_value = f'Book and {print_or_email}'
    q_o_b_dict.update(values=values, default_value=default_value)

    return q_o_b_dict


def ship_dict_from_xml(xml_file:str, config:Config):
    # inspect xml
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


def get_address_candidates(shipment:Shipment, client:DespatchBaySDK, postcode=None):
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


def address_chooser(candidates:list, client:DespatchBaySDK):
    # build address option menu dict
    address_key_dict = {}
    for candidate in candidates:
        candidate_hr = candidate.address
        address_key_dict.update({candidate_hr: candidate.key})

    # deploy address option popup using dict as mapping
    address_key = combo_popup(address_key_dict)
    if address_key:
        address = client.get_address_by_key(address_key)
        return address


def queue_shipment(client:DespatchBaySDK, shipment:Shipment, shipment_request:ShipmentRequest):
    if shipment.is_return:
        shipment.inbound_id = client.add_shipment(shipment_request)
        shipment_id = shipment.inbound_id
    else:
        shipment.outbound_id = client.add_shipment(shipment_request)
        shipment_id = shipment.outbound_id
    return shipment_id


def book_collection(shipment:Shipment, client:DespatchBaySDK, config:Config, shipment_id:str):
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
            shipment.label_location = config.labels / label_string
            label_pdf.download(shipment.label_location)
        except:
            sg.popup_error("Label not downloaded")
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        return shipment_return


def get_shipments(in_file:str, config:Config):
    # todo type hint paths? strings? both?
    shipments = []
    file_ext = in_file.split('.')[-1]
    if file_ext == 'xml':
        ship_dict = ship_dict_from_xml(in_file, config=config)
        shipments.append(Shipment(ship_dict=ship_dict))
    elif file_ext == 'dbase':
        ...
    else:
        print_and_pop("Invalid input file")
    return shipments


def get_sender_recip(shipment:Shipment, client:DespatchBaySDK):
    if shipment.is_return:
        # home address is recipient
        recipient = client.get_sender_addresses()[0]
        try:
            sender_address = client.find_address(shipment.postcode, shipment.search_term)
        except:
            candidates = get_address_candidates(client=client, shipment=shipment)
            sender_address = address_chooser(candidates=candidates, client=client)
        sender = client.sender(name=shipment.contact, email=shipment.email,
                               telephone=shipment.telephone, sender_address=sender_address)

    else:
        # home address is sender
        sender = client.get_sender_addresses()[0]
        try:
            recipient_address = client.find_address(shipment.postcode, shipment.search_term)
        except:
            candidates = get_address_candidates(shipment=shipment, client=client)
            recipient_address = address_chooser(candidates=candidates, client=client)
        recipient = client.recipient(name=shipment.contact, email=shipment.email,
                                     telephone=shipment.telephone, recipient_address=recipient_address)

    shipment.sender, shipment.recipient = sender, recipient

    return sender, recipient


def new_address_from_postcode(client:DespatchBaySDK, event:str, values:dict, shipment:Shipment, window:Window):
    """ click 'postcode' label, or press Return in postcode input to call.
        parses sender vs recipient from event code.
        takes postcode from window, gets list of candidate addresses with given postcode
        popup a chooser,
        """
    postcode = None
    mode = None
    if 'sender' in event.lower():
        mode = 'sender'
        postcode = values['-SENDER_POSTAL_CODE-']
    elif 'recipient' in event.lower():
        mode = 'recipient'
        postcode = values['-RECIPIENT_POSTAL_CODE-']

    try:
        candidates = get_address_candidates(postcode=postcode, client=client, shipment=shipment)
        chosen_address = address_chooser(candidates, client=client)
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


def update_commence(shipment:Shipment, config:Config):
    """
            runs cmclibnet via powershell script to add tracking numbes to commence db

            :return:
            """

    class CommenceEditError(Exception):
        pass

    ps_script = str(config.cmc_logger)
    try:  # utility class static method runs powershell script bypassing execuction policy
        ship_id_to_pass = str(
            shipment.inbound_id if shipment.is_return else shipment.outbound_id)
        commence_edit = Utility.powershell_runner(ps_script, shipment.category, shipment.shipment_name,
                                                  ship_id_to_pass,
                                                  str(shipment.is_return), 'debug')

        if commence_edit == 1:
            raise CommenceEditError("\nERROR: Commence Tracking not updated - is Commence running?")

    except CommenceEditError as e:
        print_and_pop(e.__repr__())

    except FileNotFoundError as e:
        print_and_pop(f"ERROR: Unable to log tracking to Commence - FileNotFoundError : {e.filename}")

    except Exception as e:
        print_and_pop(f"{e=} \nERROR: Unable to log tracking to Commence")

    else:
        ...
        # sg.popup("\nCommence Tracking updated")


def log_shipment(config:Config, shipment:Shipment):
    # export from object attrs
    shipment.boxes = len(shipment.parcels)
    export_dict = {}

    for field in config.export_fields:
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
                val = getattr(shipment, field)
                if isinstance(val, datetime):
                    val = f"{val.isoformat(sep=' ', timespec='seconds')}"

            export_dict.update({field: val})
        except Exception as e:
            print(f"{field} not found in shipment \n{e}")

    with open(config.paths['log'], 'a') as f:
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")
        sg.popup(f" Json exported to {str(f)}:\n {export_dict}")


def to_snake_case(input_string:str):
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string


def parse_amherst_address_string(str_address:str):
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


def print_and_pop(print_text: str):
    sg.popup(print_text)
    print(print_text)


def print_and_long_pop(print_string: str):
    sg.popup_scrolled(print_string)
    pprint(print_string)
