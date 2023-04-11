import dataclasses
import json
import os
import re
import xml.etree.ElementTree as ET
import time
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import Literal

import PySimpleGUI as sg
import dotenv
from fuzzywuzzy import fuzz
from PySimpleGUI import Window
from dateutil.parser import parse

from amdesp.config import Config
from amdesp.despatchbay.despatchbay_entities import ShipmentRequest, Address, ShipmentReturn, Sender, Recipient, Parcel, \
    AddressKey, Service, CollectionDate
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.despatchbay.exceptions import ApiException
from amdesp.gui_layouts import bulk_shipper_window, tracking_viewer_window, address_chooser_popup, BestMatch, \
    get_address_button_string, new_service_selector, new_date_selector, remote_address_frame, booked_shipments_frame
from amdesp.shipment import Shipment, parse_amherst_address_string
from amdesp.utils_pss.utils_pss import Utility, unsanitise

dotenv.load_dotenv()
FuzzyScores = namedtuple('FuzzyScores',
                         ['address', 'str_matched', 'customer_to_company', 'str_to_company', 'str_to_street'])


@dataclasses.dataclass
class FuzzyScoresCls:
    address: Address
    str_matched: str
    customer_to_company: str
    str_to_company: str
    str_to_street: str

    def __post_init__(self):
        self.scores = {'customer_to_company': self.customer_to_company,
                       'str_to_company': self.str_to_company,
                       'str_to_street': self.str_to_street,
                       }


class App:
    def __init__(self):
        self.shipments: [Shipment]

    def tracking_loop(self, mode: str, shipment: Shipment, client: DespatchBaySDK):
        if 'in' in mode:
            try:
                tracking_viewer_window(shipment_id=shipment.inbound_id, client=client)
            except Exception as e:
                # todo handle better
                print(f"Error while tracking inbound shipment {shipment.inbound_id}: {e}")
        elif 'out' in mode:
            try:
                tracking_viewer_window(shipment_id=shipment.outbound_id, client=client)
            except Exception as e:
                print(f"Error while tracking outbound shipment {shipment.outbound_id}: {e}")

    def go_ship_out(self, client: DespatchBaySDK, config: Config, shipments: [Shipment]):
        outbound_shipments = outbound_prep_loop(config=config, client=client, shipments=shipments)
        window = bulk_shipper_window(shipments=outbound_shipments, config=config)
        if outbound_loop(config=config, client=client, shipments=outbound_shipments, window=window) == True:
            ...


def outbound_prep_loop(config: Config, shipments: [Shipment], client: DespatchBaySDK):
    """ loops through shipments and gets sender, recipient. \n
    calls non_address_prep to get service, date, parcels and shipment requests.\n
    stores all in shipment attrs"""
    home_sender = get_home_sender(client=client, config=config)

    for shipment in shipments:
        shipment.search_term = parse_amherst_address_string(shipment.address_as_str)
        shipment.sender = home_sender
        shipment.remote_address = get_matched_address(client=client, config=config, shipment=shipment)
        shipment.recipient = get_remote_recip(client=client, shipment=shipment, remote_address=shipment.remote_address)
        try:
            non_address_prep(shipment=shipment, client=client, config=config)
        except Exception as e:
            ...
    return shipments


def outbound_loop(config: Config, shipments: [Shipment], client: DespatchBaySDK, window: Window):
    """ pysimplegui main_loop, listens for user input and updates dates, service, recipient as appropriate
    listens for go_ship  button to start booking"""
    while True:
        e, v = window.read()
        if e == sg.WIN_CLOSED or e == "Cancel":
            break

        shipment_to_edit = next(
            (shipment for shipment in shipments if shipment.shipment_name.lower() in e.lower()), None)

        if 'service' in e.lower():
            new_service = new_service_selector(shipment=shipment_to_edit)
            shipment_to_edit.service = new_service
            window[e].update(f'{new_service.name} - £{new_service.cost}')

        elif 'date' in e.lower():
            # location = window[e]
            new_collection_date = new_date_selector(shipment=shipment_to_edit, config=config)
            window[e].update(get_friendly_date(new_collection_date, config=config))
            shipment_to_edit.collection_date = new_collection_date

        elif 'recipient' in e.lower():
            old_address = shipment_to_edit.recipient.recipient_address
            new_address = address_from_user_loop(client=client, config=config, shipment=shipment_to_edit,
                                                 address=old_address)
            shipment_to_edit.recipient.recipient_address = new_address
            window[e].update(get_address_button_string(address=new_address))

        elif 'remove' in e.lower():
            shipments = [s for s in shipments if s != shipment_to_edit]
            window.close()
            window = bulk_shipper_window(shipments=shipments, config=config)
            continue

        elif e == '-GO_SHIP-':
            if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                queue_and_book(shipments=shipments, config=config, client=client)
                post_book(shipments=shipments)
                window.close()
                return True

    window.close()


def non_address_prep(shipment: Shipment, client: DespatchBaySDK, config: Config):
    """ despatchbay requires us to supply a service to get a shipment_request and a shipment_request to get an available_service. funtimes.
    so we get a service regardless of avilability, make a request, then get available services and check against pre-selected one"""
    try:
        shipment.service = get_arbitrary_service(client=client, config=config)
    except Exception as e:
        ...
    try:
        shipment.collection_date = get_collection_date(client=client, config=config, shipment=shipment)
    except Exception as e:
        ...
    try:
        shipment.parcels = get_parcels(num_parcels=shipment.boxes, client=client, config=config)
    except Exception as e:
        ...
    try:
        shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
    except Exception as e:
        ...
    try:
        shipment.service = get_actual_service(client=client, config=config, shipment=shipment)
    except Exception as e:
        ...


def get_arbitrary_service(client: DespatchBaySDK, config: Config):
    all_services = client.get_services()
    arbitrary_service = next((service for service in all_services if service.service_id == config.service_id),
                             all_services[0])
    return arbitrary_service


def get_actual_service(client: DespatchBaySDK, shipment: Shipment, config: Config):
    available_services = client.get_available_services(shipment.shipment_request)
    shipment.service_menu_map = ({service.name: service for service in available_services})
    available_service_match = next((a for a in available_services if a.service_id == config.service_id), None)
    shipment.default_service_matched = True if available_service_match else False
    shipment.available_services = available_services

    return available_service_match if available_service_match else available_services[0]


def get_remote_sender(client: DespatchBaySDK, shipment: Shipment, remote_address: Address) -> Sender:
    return client.sender(
        name=shipment.contact,
        email=shipment.email,
        telephone=shipment.telephone,
        sender_address=remote_address)


def get_remote_recip(client: DespatchBaySDK, shipment: Shipment, remote_address: Address) -> Sender:
    return client.recipient(
        name=shipment.contact,
        email=shipment.email,
        telephone=shipment.telephone,
        recipient_address=remote_address)


def quick_match(shipment: Shipment, client: DespatchBaySDK):
    for add, key in shipment.candidate_key_dict.items():
        add = add.split(',')[0]

        if add == shipment.customer:
            return client.get_address_by_key(key)
        if add == shipment.str_to_match:
            return client.get_address_by_key(key)


def get_matched_address(client: DespatchBaySDK, config: Config, shipment: Shipment) -> Address:
    """
    Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
    search by customer name, then shipment search_term
    call explicit_matches to compare strings,
    call get_bestmatch for fuzzy results,
    if best score exceed threshold ask user to confirm
    If still no valid address, call get_new_address.
    """
    address = None
    if address := search_adddress(client=client, shipment=shipment):
        return address

    shipment.candidate_key_dict = get_candidate_keys_dict(client=client, shipment=shipment, postcode=shipment.postcode)

    if address := quick_match(shipment=shipment, client=client):
        return address

    fuzzyscores = []
    for address_str, key in shipment.candidate_key_dict.items():
        candidate_address = client.get_address_by_key(key)
        if explicit_match := get_explicit_bestmatch(candidate_address=candidate_address, shipment=shipment):
            shipment.bestmatch = explicit_match
            return explicit_match.address

        else:
            fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
    else:
        # finished loop, no explicit matches so get highest scoring one from the list of fuzzyscores
        shipment.bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
        address = address_from_user_loop(client=client, config=config, shipment=shipment,
                                         address=shipment.bestmatch.address)
        return address


def search_adddress(client: DespatchBaySDK, shipment: Shipment):
    address = None
    try:
        address = client.find_address(shipment.postcode, shipment.customer)
    except ApiException:
        try:
            address = client.find_address(shipment.postcode, shipment.search_term)
        except ApiException as e:
            ...
        except Exception as e:
            sg.popup_error(e)
    except Exception as e:
        sg.popup_error(e)

    return address


def get_candidate_keys_dict(client: DespatchBaySDK, shipment: Shipment, postcode=None):
    postcode = postcode or shipment.postcode
    candidate_keys = None
    while not candidate_keys:
        try:
            candidate_keys_dict = {candidate.address: candidate.key for candidate in
                                   client.get_address_keys_by_postcode(postcode)}
        except ApiException as e:
            postcode = sg.popup_get_text(f'Bad postcode for {shipment.customer} - Please Enter')
            continue
        else:
            return candidate_keys_dict


def get_explicit_bestmatch(shipment: Shipment, candidate_address) -> BestMatch | None:
    """ if an explicit match is found return a bestmatch else None"""
    address_str_to_match = shipment.str_to_match
    if shipment.customer == candidate_address.company_name or \
            address_str_to_match == candidate_address.street:
        best_match = BestMatch(address=candidate_address, category='explicit', score=100,
                               str_matched=address_str_to_match)
        return best_match
    else:
        return None


def address_from_user_loop(client: DespatchBaySDK, config: Config, shipment: Shipment, address: Address = None):
    contact = shipment.get_sender_or_recip()

    address_frame = remote_address_frame(shipment=shipment, address=address, config=config)
    window = sg.Window('Address', layout=[[address_frame]])

    while True:
        if not window:
            break
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            return address

        if 'postal' in event.lower():
            candidates = client.get_address_keys_by_postcode(values[event.upper()])
            new_address = postcode_click(client=client, candidates=candidates)
            address_gui_from_address(address=new_address, window=window)
            continue

        if 'company_name' in event.lower():
            address = update_address_from_gui(address=address, config=config, values=values)
            setattr(address, 'company_name', shipment.customer)
            # window[event.upper()].update(shipment.customer)
            address_gui_from_address(address=address, window=window)
            continue

        if 'submit' in event.lower():
            update_contact_from_gui(config=config, contact=contact, values=values)
            address = update_address_from_gui(config=config, address=address, values=values)
            window.close()
            return address

    window.close()


def postcode_click(client: DespatchBaySDK, candidates: [AddressKey]):
    """ calls address chooser for user to select an address from those existing at either provided or shipment postcode """
    while True:
        if candidates is None:
            postcode = sg.popup_get_text("Bad Postcode - Enter Now")
            candidates = client.get_address_keys_by_postcode(postcode)
        try:
            candidate_key_dict = {candidate.address: candidate.key for candidate in candidates}
            new_address = address_chooser_popup(candidate_dict=candidate_key_dict, client=client)
        except Exception as e:
            candidates = None
            continue
        else:
            return new_address


def get_fuzzy_scores(candidate_address, shipment) -> FuzzyScoresCls:
    """" return a fuzzyscopres tuple"""
    address_str_to_match = shipment.str_to_match

    str_to_company = fuzz.partial_ratio(address_str_to_match, candidate_address.company_name)
    customer_to_company = fuzz.partial_ratio(shipment.customer, candidate_address.company_name)
    str_to_street = fuzz.partial_ratio(address_str_to_match, candidate_address.street)

    fuzzy_scores = FuzzyScoresCls(
        address=candidate_address,
        str_matched=address_str_to_match,
        customer_to_company=customer_to_company,
        str_to_company=str_to_company,
        str_to_street=str_to_street)

    return fuzzy_scores


def bestmatch_from_fuzzyscores(fuzzyscores: [FuzzyScoresCls]) -> BestMatch:
    """ return BestMatch named tuple from a list of FuzzyScores named tuples"""
    best_address = None
    best_score = 0
    best_category = ""
    str_matched = ''

    for f in fuzzyscores:
        # score_names = f.scores.keys()
        # scores = f.scores.values()
        max_category = max(f.scores, key=lambda x: f.scores[x])
        max_score = f.scores[max_category]

        if max_score > best_score:
            best_score = max_score
            best_category = max_category
            best_address = f.address
            str_matched = f.str_matched
        if max_score == 100:
            # well we wont beat that?
            break

    best_match = BestMatch(str_matched=str_matched, address=best_address, category=best_category, score=best_score)

    return best_match


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


def get_shipment_request(client: DespatchBaySDK, shipment: Shipment):
    """ returns a dbay shipment request object from shipment"""
    return client.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )


def get_collection_date(client: DespatchBaySDK, config: Config, shipment: Shipment) -> CollectionDate:
    """ return despatchbay CollecitonDate Entity"""

    available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.courier_id)
    datetime_mask = config.datetime_masks['DT_DISPLAY']

    collection_date = next(
        (date for date in available_dates if parse(date.date).date() == shipment.send_out_date),
        available_dates[0])

    for a_date in available_dates:
        date_hr = f'{parse(a_date.date):{datetime_mask}}'
        shipment.date_menu_map.update({date_hr: a_date})

    return collection_date


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


def get_service(client: DespatchBaySDK, config: Config, shipment: Shipment):
    services = client.get_services()

    # todo get AVAILABLE services needs a request
    # services = client.get_available_services()
    # shipment.service_menu_map.update({service.name: service for service in services})

    return next((service for service in services if service.service_id == config.service_id),
                services[0])


def email_label():
    # todo this
    ...


def setup_commence(config: Config):
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


def get_parcels(num_parcels: int, client: DespatchBaySDK, config: Config) -> list[Parcel]:
    """ return an array of dbay parcel objects equal to the number of boxes provided
        uses arbitrary sizes because dbay api wont allow skipping even though website does"""
    parcels = []
    for x in range(num_parcels):
        parcel = client.parcel(
            contents=config.home_address['parcel_contents'],
            value=500,
            weight=6,
            length=60,
            width=40,
            height=40,
        )
        parcels.append(parcel)
    return parcels


def book_shipment(client: DespatchBaySDK, shipment: Shipment, shipment_id: str):
    try:
        shipment_return = client.book_shipments(shipment_id)[0]
    except:
        sg.popup_error(f"Unable to Book {shipment.shipment_name}")
    else:
        shipment.collection_booked = True
        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        return shipment_return


# def bulk_book(client: DespatchBaySDK, shipments: [Shipment], shipment_id: str):
#     for shipment in shipments:
#         try:
#             shipment.shipment_return = client.book_shipments(shipment_id)[0]
#         except:
#             sg.popup_error(f"Unable to Book {shipment.shipment_name}")
#         else:
#             shipment.collection_booked = True
#             shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"

def queue_and_book(shipments: [Shipment], client: DespatchBaySDK, config: Config):
    for shipment in shipments:

        if not config.sandbox:
            if not sg.popup_yes_no('NOT SANDBOX - PAYING FOR MANY!!') == 'Yes':
                return None
        try:
            shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
            shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
            id_to_log = client.add_shipment(shipment.shipment_request)
            setattr(shipment, f'{"inbound_id" if shipment.is_return else "outbound_id"}', id_to_log)
            shipment.shipment_return = book_shipment(client=client, shipment=shipment, shipment_id=id_to_log)
            shipment.collection_booked = True
            download_label(client=client, config=config, shipment=shipment)
            print_label(shipment=shipment)
            update_commence(config=config, shipment=shipment)
            log_shipment(config=config, shipment=shipment)
        except Exception as e:
            sg.popup_error(f"Error with{shipment.shipment_name}"
                           f"Error = {e}")

def post_book(shipments:[Shipment]):
    frame = booked_shipments_frame(shipments=shipments)
    window2 = sg.Window('', layout=[[frame]])
    while True:
        e2, v2 = window2.read()
        if e2 in [sg.WIN_CLOSED, 'Exit']:
            window2.close()

        window2.close()
        break

def download_label(client: DespatchBaySDK, config: Config, shipment: Shipment):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name}.pdf at location specified in config.toml"""
    try:
        label_pdf = client.get_labels(shipment.shipment_return.shipment_document_id, label_layout='2A4')
        label_string = shipment.shipment_name + '.pdf'
        shipment.label_location = config.labels / label_string
        label_pdf.download(shipment.label_location)
    except:
        return False
    else:
        return True


#
# def contact_gui_from_contact(config: Config, contact: Sender | Recipient, window: Window):
#     """ updates gui with contact details for sender or recipient"""
#     for field in config.contact_fields:
#         value = getattr(contact, field, None)
#         window[f'-CONTACT_{field.upper()}-'].update(value)


def address_gui_from_address(address: Address, window: Window):
    address_dict = {k: v for k, v in vars(address).items() if 'soap' not in k}
    address_dict.pop('country_code', None)
    for k, v in address_dict.items():
        window[f'-{k.upper()}-'].update(v or '')


def update_address_from_gui(config: Config, address: Address, values: dict):
    address_fields = config.address_fields
    for field in address_fields:
        value = values.get(f'-{field.upper()}-', None)
        setattr(address, field, value)
    return address


def update_contact_from_gui(config: Config, contact: Sender | Recipient, values: dict):
    contact_fields = config.contact_fields
    contact_type = type(contact).__name__
    for field in contact_fields:
        value = values.get(f'-{contact_type}_{field}-'.upper())
        setattr(contact, field, value)


def update_commence(config: Config, shipment: Shipment):
    """ runs cmclibnet via powershell script to add shipment_id to commence db """

    ps_script = str(config.cmc_logger)
    try:  # utility class static method runs powershell script bypassing execuction policy
        ship_id_to_pass = str(
            shipment.inbound_id if shipment.is_return else shipment.outbound_id)
        commence_edit = Utility.powershell_runner(ps_script, shipment.category, shipment.shipment_name,
                                                  ship_id_to_pass,
                                                  str(shipment.is_return), 'debug')
    except Exception as e:
        ...
    else:
        if commence_edit == 0:
            shipment.loged_to_commence = True
    return shipment.loged_to_commence


def print_label(shipment):
    """ prints the labels stored at shipment.label_location """
    try:
        os.startfile(str(shipment.label_location), "print")
    except Exception as e:
        return False
    else:
        shipment.printed = True
        return True


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
        # sg.popup(f" Json exported to {str(f)}:\n {export_dict}")


def print_and_pop(print_text: str):
    sg.popup(print_text)
    print(print_text)


def print_and_long_pop(print_string: str):
    sg.popup_scrolled(print_string)
    pprint(print_string)


def get_friendly_date(collection_date, config: Config):
    return f'{parse(collection_date.date):{config.datetime_masks["DT_DISPLAY"]}}'
