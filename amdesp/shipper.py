import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pprint import pprint
from typing import Literal

import PySimpleGUI as sg
import dotenv
from PySimpleGUI import Window
from dateutil.parser import parse

from amdesp.config import Config
from amdesp.despatchbay.despatchbay_entities import ShipmentRequest, Address, ShipmentReturn, Sender, Recipient, Parcel
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.despatchbay.exceptions import ApiException
from amdesp.gui_layouts import main_window, tracking_viewer_window, address_chooser_popup
from amdesp.shipment import Shipment, parse_amherst_address_string
from amdesp.utils_pss.utils_pss import Utility, unsanitise

dotenv.load_dotenv()


class App:
    def __init__(self):
        self.shipments: [Shipment]

    def main_loop(self, client: DespatchBaySDK, config: Config, sandbox: bool, shipment: Shipment):
        if sandbox:
            sg.theme('Tan')
        else:
            sg.theme('Dark Blue')

        window = main_window()
        populate_home_address(client=client, config=config, shipment=shipment, window=window)
        populate_remote_address(client=client, config=config, shipment=shipment, window=window)
        populate_non_address_fields(client=client, config=config, shipment=shipment, window=window)

        while True:
            window['-SENDER_POSTAL_CODE-'].bind("<Return>", '')
            window['-RECIPIENT_POSTAL_CODE-'].bind("<Return>", '')
            if not window:
                # prevent crash on exit
                break
            event, values = window.read()

            if event in (sg.WINDOW_CLOSED, 'Exit'):
                break

            # click company name to copy customer in
            if 'company_name' in event:
                window[event.upper()].update(shipment.customer)

            # click 'postcode' or enter 'Return' in postcode box to list and choose from addresses at postcode
            if 'postal_code' in event.lower():
                self.postcode_click(client, event, values, window)

            # click existing shipment id to track shipping
            if event == '-INBOUND_ID-':
                tracking_viewer_window(shipment.inbound_id, client=client)
            if event == '-OUTBOUND_ID-':
                tracking_viewer_window(shipment.outbound_id, client=client)

            if event == '-GO-':
                decision = values['-QUEUE_OR_BOOK-'].lower()
                if 'queue' or 'book' in decision:
                    shipment_request = make_request(client=client, shipment=shipment, values=values)
                    answer = sg.popup_scrolled(f"{decision}?\n{shipment_request}", size=(30, 30))

                    # todo remove safety checks when ship
                    if answer == 'OK':
                        if not sandbox:
                            if not sg.popup("NOT SANDBOX DO YOU WANT TO PAY?!!!") == 'OK':
                                continue

                        # queue shipment
                        shipment_id = queue_shipment(shipment_request=shipment_request, shipment=shipment,
                                                     client=client)
                        if 'book' in decision:
                            shipment_return = book_collection(client=client, config=config, shipment=shipment,
                                                              shipment_id=shipment_id)
                            download_label(client=client, config=config, shipment_return=shipment_return,
                                           shipment=shipment)

                        if 'print' in decision:
                            print_label(shipment=shipment)

                        if 'email' in decision:
                            ...  # todo implement this, which email client?

                        # log shipment id to commence database
                        update_commence(config=config, shipment=shipment)

                        # log to json
                        log_shipment(config=config, shipment=shipment)
                        break

        window.close()

    def postcode_click(self, client, event, values, window):
        new_address = get_new_address(client=client, postcode=values[event.upper()])
        if new_address:
            sender_or_recip = 'sender' if 'sender' in event.lower() else 'recipient'
            update_address_gui(address=new_address, window=window, sender_or_recip=sender_or_recip)


def get_remote_address(client: DespatchBaySDK, shipment: Shipment) -> Address:
    """
    Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
    If supplied data does not yield a valid address, call get_new_address.
    """
    try:
        address = client.find_address(shipment.postcode, shipment.customer)
    except ApiException:
        try:
            address = client.find_address(shipment.postcode, shipment.search_term)
        except:
            address = None

    while not address:
        if sg.popup_yes_no("No address - try again?") == "Yes":
            address = get_new_address(client=client, postcode=shipment.postcode)
        else:
            sg.popup_error("Well if you don't have an address I guess I'll crash now.\nGoodbye")
            break
    return address


def get_remote_sender(shipment: Shipment, address: Address,
                      client: DespatchBaySDK) -> Sender:
    """ return a dbay sender object for the given address and shipment contact details"""
    sender = client.sender(
        name=shipment.contact,
        email=shipment.email,
        telephone=shipment.telephone,
        sender_address=address)
    return sender


def get_remote_recipient(shipment: Shipment, address: Address,
                         client: DespatchBaySDK) -> Recipient:
    """ return a dbay recipient object for the given address and shipment contact details"""
    recipient = client.recipient(
        name=shipment.contact,
        email=shipment.email,
        telephone=shipment.telephone,
        recipient_address=address)
    return recipient


#
# def get_remote_sender_or_recip(sender_or_recip: Literal['sender', 'recipient'], shipment: Shipment, address: Address,
#                                client: DespatchBaySDK) -> [Sender | Recipient]:
#     if sender_or_recip == 'recipient':
#         recipient_or_sender = client.recipient(
#             name=shipment.contact,
#             email=shipment.email,
#             telephone=shipment.telephone,
#             recipient_address=address
#         )
#     else:
#         recipient_or_sender = client.sender(
#             name=shipment.contact,
#             email=shipment.email,
#             telephone=shipment.telephone,
#             sender_address=address
#         )
# 
#     return recipient_or_sender


def get_home_sender(client: DespatchBaySDK, config: Config) -> Sender:
    """ return a dbay sender object representing home address defined in toml"""
    return client.sender(
        address_id=config.home_sender_id,
        name=config.home_address['contact'],
        email=config.home_address['email'],
        telephone=config.home_address['telephone'],
        sender_address=client.get_sender_addresses()[0].sender_address
    )


def get_home_recipient(client: DespatchBaySDK, config: Config) -> Recipient:
    """ return a dbay recipient object representing home address defined in toml"""
    return client.recipient(
        name=config.home_address['contact'],
        email=config.home_address['email'],
        telephone=config.home_address['telephone'],
        recipient_address=client.find_address(config.home_address['postal_code'],
                                              config.home_address['search_term'])
    )


def make_request(client: DespatchBaySDK, shipment: Shipment, values: dict) -> ShipmentRequest:
    """ retrieves values from gui and returns a dbay shipment request object """
    shipment.parcels = get_parcels(values['-BOXES-'], client=client, shipment=shipment)
    shipment.date = shipment.date_menu_map.get(values['-DATE-'])
    shipment.service = shipment.service_menu_map.get(values['-SERVICE-'])
    # todo update address from values

    shipment_request = client.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer,
        collection_date=shipment.date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )
    return shipment_request


def get_dates_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
    """ get available collection dates as dbay collection date objects for shipment.sender.address
        construct a menu_def for a combo-box
        if desired send-date matches an available date then select it as default, otherwise select soonest colelction
        return a dict with values and default_value"""

    # potential dates as dbay objs not proper datetime objs
    available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.courier_id)
    datetime_mask = config.datetime_masks['DT_DISPLAY']

    chosen_collection_date_dbay = next((date for date in available_dates if parse(date.date) == shipment.date),
                                       available_dates[0])

    chosen_date_hr = f'{parse(chosen_collection_date_dbay.date):{datetime_mask}}'
    shipment.date_menu_map.update({f'{parse(date.date):{datetime_mask}}': date for date in available_dates})
    men_def = [f'{parse(date.date):{datetime_mask}}' for date in available_dates]

    shipment.date = chosen_collection_date_dbay
    return {'default_value': chosen_date_hr, 'values': men_def}


def get_service_menu(client: DespatchBaySDK, config: Config, shipment: Shipment):
    """ gets available shipping services for shipment sender and recipient
    builds menu_def of options and if any matches service_id specified in config.toml then select it by default
     return a dict of menu_def and default_value"""
    services = client.get_services()
    # todo get AVAILABLE services needs a request
    # services = client.get_available_services()
    shipment.service_menu_map.update({service.name: service for service in services})
    chosen_service = next((service for service in services if service.service_id == config.service_id), services[0])
    if not chosen_service:
        print_and_pop("Default service unavailable")
    shipment.service = chosen_service

    return {'values': [service.name for service in services], 'default_value': chosen_service.name}


def populate_non_address_fields(client: DespatchBaySDK, config: Config, shipment: Shipment, window: Window):
    """ fills gui from shipment details. if customer address is invalid launch a popup to fix"""

    services_dict = get_service_menu(client=client, config=config, shipment=shipment)
    dates_dict = get_dates_menu(client=client, config=config, shipment=shipment)
    q_o_b_dict = get_queue_or_book_menu(shipment=shipment)

    window['-SHIPMENT_NAME-'].update(shipment.shipment_name)
    # todo color date based on match.... how to update without bg-color in update method? = learn TKinter
    window['-DATE-'].update(values=dates_dict['values'], value=dates_dict['default_value'])
    window['-SERVICE-'].update(values=services_dict['values'], value=services_dict['default_value'])
    if shipment.inbound_id:
        window['-INBOUND_ID-'].update(shipment.inbound_id, enable_events=True)
    if shipment.outbound_id:
        window['-OUTBOUND_ID-'].update(shipment.outbound_id, enable_events=True)
    window['-QUEUE_OR_BOOK-'].update(values=q_o_b_dict['values'], value=q_o_b_dict['default_value'])
    window['-BOXES-'].update(value=shipment.boxes or 1)


def populate_home_address(client: DespatchBaySDK, config: Config, shipment: Shipment,
                          window: Window):
    """ updates shipment and gui window with homebase contact and address details in sender or recipient position as appropriate"""
    if shipment.is_return:
        shipment.recipient = get_home_recipient(client=client, config=config)
        update_contact_gui(config=config, sender_or_recip=shipment.recipient, window=window)
        update_address_gui(address=shipment.recipient.recipient_address, sender_or_recip='recipient',
                           window=window)
    else:
        shipment.sender = get_home_sender(client=client, config=config)
        update_contact_gui(config=config, sender_or_recip=shipment.sender, window=window)
        update_address_gui(address=shipment.sender.sender_address, sender_or_recip='sender', window=window)


def populate_remote_address(client: DespatchBaySDK, config: Config, shipment: Shipment, window: Window):
    """ updates shipment and gui window with customer contact and address details in sender or recipient position as appropriate"""
    remote_address = get_remote_address(client=client, shipment=shipment)
    if shipment.is_return:
        shipment.sender = get_remote_sender(client=client, shipment=shipment, address=remote_address)
        update_contact_gui(config=config, sender_or_recip=shipment.sender, window=window)
        update_address_gui(address=shipment.sender.sender_address, sender_or_recip='sender', window=window)

    else:
        shipment.recipient = get_remote_recipient(client=client, shipment=shipment, address=remote_address)
        update_contact_gui(config=config, sender_or_recip=shipment.recipient, window=window)
        update_address_gui(address=shipment.recipient.recipient_address, sender_or_recip='recipient',
                           window=window)


def email_label():
    # todo this
    ...


def setup_commence(config: Config()):
    """ looks for CmcLibNet in prog files, if absent attempts to install exe located at path defined in config.toml"""
    try:
        if not config.cmc_dll.exists():
            raise FileNotFoundError("CmcLibNet not installed - launching setup.exe")
    except Exception as e:
        try:
            config.install_cmc_lib_net()
        except Exception as e:
            print_and_pop("Unable to find or install CmcLibNet - logging to commence is impossible")
            # error message built into cmclibnet installer


def get_parcels(num_parcels: int, client: DespatchBaySDK, shipment: Shipment) -> list[Parcel]:
    """ return an array of dbay parcel objects equal to the number of boxes provided
        uses arbitrary sizes because dbay api wont allow skipping even though website does"""
    parcels = []
    for x in range(num_parcels):
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


def get_queue_or_book_menu(shipment: Shipment) -> dict:
    """ construct menu options for queue / book / print etc
        return values and default value"""
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


def queue_shipment(client: DespatchBaySDK, shipment: Shipment, shipment_request: ShipmentRequest) -> str:
    """ queues a shipment specified by the provided dbay shipment_request object
        returns the shipment id for tracking purposes"""
    if shipment.is_return:
        shipment.inbound_id = client.add_shipment(shipment_request)
        shipment_id = shipment.inbound_id
    else:
        shipment.outbound_id = client.add_shipment(shipment_request)
        shipment_id = shipment.outbound_id
    return shipment_id


def book_collection(client: DespatchBaySDK, config: Config, shipment: Shipment,
                    shipment_id: str) -> ShipmentReturn | None:
    """ books collection of shipment specified by provided shipment id"""
    try:
        shipment_return = client.book_shipments(shipment_id)[0]
    except:
        sg.popup_error("Unable to Book")
        # return None
    else:
        shipment.collection_booked = True
        sg.popup_scrolled(f'Shipment booked: \n{shipment_return}', size=(20, 20))
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        return shipment_return


def download_label(client: DespatchBaySDK, config: Config, shipment_return: ShipmentReturn, shipment: Shipment):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name}.pdf at location specified in config.toml"""
    try:
        label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
        label_string = shipment.shipment_name.replace(r'/', '-') + '.pdf'
        shipment.label_location = config.labels / label_string
        label_pdf.download(shipment.label_location)
    except:
        sg.popup_error("Label not downloaded")


def print_label(shipment):
    """ prints the labels stored at shipment.label_location """
    try:
        os.startfile(str(shipment.label_location), "print")
    except Exception as e:
        sg.popup_error(f"\n ERROR: Unable to print \n{e}")
    else:
        shipment.printed = True


def get_shipments(config: Config, in_file: str) -> list:
    """ parses input filetype and calls appropriate function to construct and return a list of shipment objects"""
    shipments = []
    file_ext = in_file.split('.')[-1]
    if file_ext == 'xml':
        ship_dict = ship_dict_from_xml(config=config, xml_file=in_file)
        try:
            shipments.append(Shipment(ship_dict=ship_dict))
        except KeyError as e:
            print(f"Shipdict Key missing: {e}")
    elif file_ext == 'dbase':
        ...
    else:
        print_and_pop("Invalid input file")
    return shipments


def get_new_address(client: DespatchBaySDK, postcode: str = None) -> Address:
    """ calls address chooser for user to select an address from those existing at either provided or shipment postcode """
    while True:
        postcode = postcode or sg.popup_get_text("Bad Postcode - please enter")
        try:
            candidates = client.get_address_keys_by_postcode(postcode)
        except:
            postcode = None
            continue
        else:
            address = address_chooser(candidates=candidates, client=client)
            return address


def address_chooser(candidates: list, client: DespatchBaySDK) -> Address:
    """ returns an address as chosen by user from a given list of candidates"""
    # build address option menu dict
    address_key_dict = {candidate.address: candidate.key for candidate in candidates}
    # for candidate in candidates:
    #     address_key_dict.update({candidate.address: candidate.key})

    # deploy address option popup using dict as mapping
    address_key = address_chooser_popup(address_key_dict)
    if address_key:
        address = client.get_address_by_key(address_key)
        return address


def update_contact_gui(config: Config, sender_or_recip: Sender | Recipient, window: Window):
    """ updates gui with contact details for given sender or recipient object"""
    for field in config.contact_fields:
        value = getattr(sender_or_recip, field, None)
        window[f'-{type(sender_or_recip).__name__.upper()}_{field.upper()}-'].update(value)


def update_address_gui(address: Address, sender_or_recip: str, window: Window, client: DespatchBaySDK = None):
    address_dict = {k: v for k, v in vars(address).items() if 'soap' not in k}
    address_dict.pop('country_code', None)
    for k, v in address_dict.items():
        window[f'-{sender_or_recip.upper()}_{k.upper()}-'].update(v or '')


def update_commence(config: Config, shipment: Shipment):
    """ runs cmclibnet via powershell script to add shipment_id to commence db """

    ps_script = str(config.cmc_logger)
    try:  # utility class static method runs powershell script bypassing execuction policy
        ship_id_to_pass = str(
            shipment.inbound_id if shipment.is_return else shipment.outbound_id)
        commence_edit = Utility.powershell_runner(ps_script, shipment.category, shipment.shipment_name,
                                                  ship_id_to_pass,
                                                  str(shipment.is_return), 'debug')

        if commence_edit == 1:
            raise Exception("\nERROR: Commence Tracking not updated - is Commence running?")

    except FileNotFoundError as e:
        print_and_pop(f"ERROR: Unable to log tracking to Commence - FileNotFoundError : {e.filename}")

    except Exception as e:
        print_and_pop(f"{e=} \nERROR: Unable to log tracking to Commence")


def log_shipment(config: Config, shipment: Shipment):
    # export from object attrs
    shipment.boxes = len(shipment.parcels)
    export_dict = {}

    for field in config.export_fields:
        try:
            if field == 'sender':
                val = shipment.sender.__repr__()
            elif field == 'recipient':
                val = shipment.recipient.__repr__()
            else:
                val = getattr(shipment, field)
                if isinstance(val, datetime):
                    val = f"{val.isoformat(sep=' ', timespec='seconds')}"

            export_dict.update({field: val})
        except Exception as e:
            print(f"{field} not found in shipment \n{e}")

    with open(config.log_json, 'a') as f:
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")
        sg.popup(f" Json exported to {str(f)}:\n {export_dict}")


def ship_dict_from_xml(config: Config, xml_file: str) -> dict:
    """parse amherst shipment xml"""
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

            if "number" in k.lower():
                v = int(v.replace(',', ''))
            if k == 'name':
                k = 'shipment_name'
            if k[:6] == "deliv ":
                k = k.replace('deliv', 'delivery')
            k = k.replace('delivery_', '')
            if k == 'tel':
                k = 'telephone'
            if k == 'address':
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

    # convert send-out-date to dt object, or insert today
    ship_dict['send_out_date'] = ship_dict.get('send_out_date', None)
    if ship_dict['send_out_date']:
        # ship_dict['send_out_date'] = parse(ship_dict['send_out_date'])
        ship_dict['send_out_date'] = datetime.strptime(ship_dict['send_out_date'], config.datetime_masks['DT_HIRE'])
    else:
        ship_dict['send_out_date'] = datetime.today()

    ship_dict['category'] = category
    ship_dict['search_term'] = parse_amherst_address_string(ship_dict['address_as_str'])

    ship_dict['boxes'] = ship_dict.get('boxes', 1)

    missing = []
    for attr_name in shipment_fields:
        if attr_name not in ship_dict.keys():
            if attr_name not in ['cost', 'inbound_id', 'outbound_id']:
                missing.append(attr_name)
    if missing:
        print_and_pop(f"*** Warning - {missing} not found in ship_dict - Warning ***")
    return ship_dict


def to_snake_case(input_string: str) -> str:
    """Convert a string to lowercase snake case."""
    input_string = input_string.replace(" ", "_")
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    input_string = input_string.lower()
    return input_string


def print_and_pop(print_text: str):
    sg.popup(print_text)
    print(print_text)


def print_and_long_pop(print_string: str):
    sg.popup_scrolled(print_string)
    pprint(print_string)
