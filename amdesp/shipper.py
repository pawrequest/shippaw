import dataclasses
import json
import logging
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path

import PySimpleGUI as sg
import dotenv
from fuzzywuzzy import fuzz
from dateutil.parser import parse

from amdesp.config import Config
from amdesp.despatchbay.despatchbay_entities import Address, Sender, Recipient, Parcel, AddressKey, Service, \
    CollectionDate
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from amdesp.despatchbay.documents_client import Document
from amdesp.despatchbay.exceptions import ApiException
from amdesp.exceptions import WindowClosedError

from amdesp.gui_layouts import BestMatch, get_address_button_string, new_date_selector, new_service_selector, \
    address_chooser_popup, tracking_viewer_window, compare_addresses_window, get_contact_frame, bulk_shipper_window, \
    booked_shipments_frame, get_date_label
from amdesp.shipment import Shipment
from amdesp.utils_pss.utils_pss import Utility

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
LIMITED_SHIPMENTS = 1


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


class ShipMode(Enum):
    ship_out, ship_in, track_in, track_out = range(1, 5)


class Shipper:
    def __init__(self, config: Config):
        self.config = config
        self.shipments: [Shipment] = []

    def dispatch(self, client: DespatchBaySDK, mode: str, in_file: str):
        # loading = gui.loading()
        sg.popup_quick_message('loading shipments', keep_on_top=True)
        try:
            if 'ship' in mode:
                shipments = Shipment.get_shipments(config=self.config, in_file=in_file)
                prepped_shipments = self.prep_shipments(client=client, mode=mode, shipments=shipments)
                window = bulk_shipper_window(shipments=prepped_shipments, config=self.config)
                # loading.close()
                booked_shipments = self.gui_loop(shipments=prepped_shipments, window=window, client=client)
                post_cleanup = self.post_book(shipments=booked_shipments)
            elif 'track' in mode:
                # loading.close()
                # tracking_loop(mode=mode, shipment=)
                ...
            else:
                # loading.close()

                ...
        except Exception as e:
            # loading.close()
            ...
        if sg.popup_yes_no("Close?") == 'Yes':
            exit()

    def tracking_loop(self, mode: str, shipment: Shipment, client: DespatchBaySDK):
        if 'in' in mode:
            try:
                tracking_viewer_window(shipment_id=shipment.inbound_id, client=client)
            except Exception as e:
                # todo handle better
                logger.critical(f"Error while tracking inbound shipment {shipment.inbound_id}: {e}")
        elif 'out' in mode:
            try:
                tracking_viewer_window(shipment_id=shipment.outbound_id, client=client)
            except Exception as e:
                logger.critical(f"Error while tracking outbound shipment {shipment.outbound_id}: {e}")

    def prep_shipments(self, client: DespatchBaySDK, mode: str, shipments: {Shipment}):
        """  gets sender, recipient, service, date, parcels and shipment request objects from dbay api \n

        stores all in shipment attrs"""
        prepped_shipments = []
        config = self.config
        outbound = mode == 'ship_out'

        home_sender_recip = get_home_sender(client=client, config=config) if outbound \
            else get_home_recipient(client=client, config=config)
        logger.info(f'PREP SHIPMENT -  {home_sender_recip=}')

        if LIMITED_SHIPMENTS:
            shipments = shipments[0:LIMITED_SHIPMENTS]
        for shipment in shipments:
            # for shipment in shipments[0:2]:
            sg.popup_quick_message(f'Preparing {shipment.shipment_name}', keep_on_top=True)
            try:
                remote_address = self.get_remote_address(shipment=shipment, client=client)
                logger.info(f'PREP SHIPMENT {shipment.shipment_name} - {remote_address=}')

                shipment.sender = home_sender_recip if outbound else remote_address
                shipment.recipient = get_remote_recip(client=client, shipment=shipment, remote_address=remote_address) \
                    if outbound else home_sender_recip

                logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {shipment.recipient}')

                shipment.service = get_arbitrary_service(client=client, config=self.config)
                logger.info(f'PREP SHIPMENT - ARBITRARY SERVICE {shipment.service.name}')

                logger.info(f'PREP SHIPMENT - CHECK TODAY SHIP {shipment.send_out_date}')
                shipment = check_today_ship(shipment)
                if not shipment:
                    logger.info(f'PREPPING SHIPMENT - CHECK TODAY SHIP - CANCEL SHIPMENT')
                    continue

                shipment.collection_date = get_collection_date(client=client, config=self.config, shipment=shipment)
                logger.info(f'PREPPING SHIPMENT - COLLECTION DATE {shipment.collection_date}')

                shipment.parcels = get_parcels(num_parcels=shipment.boxes, client=client, config=self.config)
                logger.info(f'PREPPING SHIPMENT - PARCELS {shipment.parcels}')

                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
                logger.info(f'PREPPING SHIPMENT - SHIPMENT REQUEST {shipment.shipment_request}')

                shipment.service = get_actual_service(client=client, config=self.config, shipment=shipment)
                logger.info(f'PREPPING SHIPMENT - ACTUAL SERVICE {shipment.service.name}')

                prepped_shipments.append(shipment)

            except Exception as e:
                shipments.pop(shipment)
                logger.error(f'Error with {shipment.shipment_name}:\n'
                             f'{e}')
                continue

        return prepped_shipments

    def get_remote_address(self, client: DespatchBaySDK, shipment: Shipment) -> Address:
        """ returns an address, tries by direct search, quick address string comparison, explicit BestMatch, BestMatch from FuzzyScores, or finally user input  """
        config = self.config
        candidate_keys = None

        address = search_adddress(client=client, shipment=shipment)
        logger.info(f"SEARCH MATCHED ADDRESS : {address}") if address else None

        if not address:
            candidate_keys = get_candidate_keys_dict(client=client, shipment=shipment)
            address = quick_match(shipment=shipment, client=client, candidate_key_dict=candidate_keys)
            logger.info(f"QUICKMATCH ADDRESS : {address}") if address else None

        if not address:
            bestmatch = get_bestmatch(client=client, candidate_key_dict=candidate_keys, shipment=shipment)
            logger.info(f"BESTMATCH : {bestmatch}") if bestmatch else None
            address = bestmatch.address

        if address:
            address = check_address_company(address=address, shipment=shipment, config=config)
            logger.info(f'CHECK ADDRESS COMPANY : {address if address else ""}')

        if not address:
            candidate_keys = candidate_keys or get_candidate_keys_dict(client=client, shipment=shipment)
            bestmatch = get_bestmatch(candidate_key_dict=candidate_keys, shipment=shipment, client=client)
            logger.info(f"BESTMATCH FROM KEYS : {bestmatch}") if bestmatch else None

            address = self.address_gui_loop(address=bestmatch.address, shipment=shipment, client=client)
        return address

    def gui_loop(self, client: DespatchBaySDK, shipments: [Shipment], window: sg.Window):
        """ pysimplegui main_loop, takes a prebuilt window and shipment list,
        listens for user input and updates shipments
        listens for go_ship  button to start booking"""
        config = self.config

        while True:
            e, v = window.read()
            if e == sg.WIN_CLOSED or e == "Cancel":
                raise WindowClosedError

            shipment_to_edit: Shipment = next((shipment for shipment in shipments
                                               if shipment.shipment_name.lower() in e.lower()), None)

            if 'boxes' in e.lower():
                if new_boxes := get_new_parcels(client=client, config=config, location=window.mouse_location()):
                    shipment_to_edit.parcels = new_boxes
                    window[e].update(f'{len(shipment_to_edit.parcels)}')
                    window[f'-{shipment_to_edit.shipment_name}_SERVICE-'.upper()].update(
                        f'{shipment_to_edit.service.name} \n£{len(new_boxes) * shipment_to_edit.service.cost}')

            if 'service' in e.lower():
                num_boxes = len(shipment_to_edit.parcels)
                new_service = new_service_selector(shipment=shipment_to_edit, location=window.mouse_location())
                shipment_to_edit.service = new_service
                # window[e].update(f'{new_service.name} - £{new_service.cost}')
                window[e].update(f'{new_service.name}\n{num_boxes * new_service.cost}')

            elif 'date' in e.lower():
                # location = window[e]
                new_collection_date = new_date_selector(shipment=shipment_to_edit, config=config,
                                                        location=window.mouse_location())
                window[e].update(get_date_label(new_collection_date, config=config))
                shipment_to_edit.collection_date = new_collection_date

            elif 'recipient' in e.lower():
                old_address = shipment_to_edit.recipient.recipient_address
                # possy = window[e][]
                new_address = self.address_gui_loop(shipment=shipment_to_edit, address=old_address, client=client)
                shipment_to_edit.recipient.recipient_address = new_address
                window[e].update(get_address_button_string(address=new_address))

            elif 'remove' in e.lower():
                shipments = [s for s in shipments if s != shipment_to_edit]
                window.close()
                window = bulk_shipper_window(shipments=shipments, config=config)
                continue

            elif e == '-GO_SHIP-':
                if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                    if booked_ship := self.queue_and_book(shipments=shipments, client=client):
                        window.close()
                        return booked_ship

        window.close()

    def address_gui_loop(self, client: DespatchBaySDK, address: Address, shipment: Shipment) -> Address:
        """ Gui loop, takes an address and shipment for contact details,
        allows editing / replacing before returning address"""

        config = self.config
        # contact = shipment.get_sender_or_recip()

        address_frame = get_contact_frame(shipment=shipment, address=address, config=config)
        window = sg.Window('Address', layout=[[address_frame]])

        while True:
            if not window:
                break
            event, values = window.read()
            if event in (sg.WINDOW_CLOSED, 'Exit'):
                return address

            if 'postal' in event.lower():
                candidates = client.get_address_keys_by_postcode(values[event.upper()])
                new_address = self.postcode_click(client=client, candidates=candidates)
                address_gui_from_address(address=new_address, window=window)
                continue

            if 'company_name' in event.lower():
                address = update_address_from_gui(address=address, config=config, values=values)
                setattr(address, 'company_name', shipment.customer)
                # window[event.upper()].update(shipment.customer)
                address_gui_from_address(address=address, window=window)
                continue

            if 'submit' in event.lower():
                # update_remote_address_from_gui(config=config, values=values)
                address = update_address_from_gui(config=config, address=address, values=values)
                window.close()
                return address

        window.close()

    def postcode_click(self, client: DespatchBaySDK, candidates: [AddressKey]):

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


    def queue_and_book(self, client: DespatchBaySDK, shipments: [Shipment]):
        config = self.config
        booked_shipments = []

        for shipment in shipments:

            if not config.sandbox:
                if not sg.popup_yes_no('NOT SANDBOX - PAYING FOR MANY!!') == 'Yes':
                    return None
            try:
                shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)

                sg.popup_quick_message(f'Adding shipment {shipment.shipment_name}', keep_on_top=True)
                shipment_id = client.add_shipment(shipment.shipment_request)
                setattr(shipment, f'{"inbound_id" if shipment.is_return else "outbound_id"}', shipment_id)

                sg.popup_quick_message(f'Booking shipment {shipment.shipment_name}', keep_on_top=True)
                shipment_return = book_shipment(client=client, shipment=shipment, shipment_id=shipment_id)
                shipment.shipment_return = shipment_return

                sg.popup_quick_message(f'Downloading Label {shipment.shipment_name}', keep_on_top=True)
                download_label(client=client, config=config, shipment=shipment)

                sg.popup_quick_message(f'Printing Label {shipment.shipment_name}', keep_on_top=True)
                print_label(shipment=shipment)

                update_commence(config=config, shipment=shipment, id_to_pass=shipment_id)
                booked_shipments.append(shipment)
                log_shipment(config=config, shipment=shipment)
                continue

            except ApiException as e:
                sg.popup_error(f"Unable to Book {shipment.shipment_name}\n"
                               f"\nServer returned the following error:\n"
                               f"{e}\n"
                               f"\nThat probably didn't help?\n"
                               f"How about this?:\n"
                               f"Available balance = £{client.get_account_balance().available}\n")
                continue

        return booked_shipments if booked_shipments else None

    @staticmethod
    def post_book(shipments: [Shipment]):
        headers = []
        frame = booked_shipments_frame(shipments=shipments)
        window2 = sg.Window('Booking Results:', layout=[[frame]])
        while True:
            e2, v2 = window2.read()
            if e2 in [sg.WIN_CLOSED, 'Exit']:
                window2.close()

            window2.close()
            break


def get_new_parcels(client: DespatchBaySDK, config: Config, location):
    # new_boxes = sg.popup_get_text("Enter a number")
    layout = [
        [sg.Combo(values=[i for i in range(1, 10)], enable_events=True, expand_x=True, readonly=True, default_value=1,
                  k='BOX')]
    ]
    window = sg.Window('', layout=layout, location=location, relative_location=(-50, -50))
    e, v = window.read()
    if e == sg.WIN_CLOSED:
        window.close()
    if e == 'BOX':
        new_boxes = v[e]
        window.close()
        if parcels := get_parcels(int(new_boxes), client=client, config=config):
            return parcels


def get_arbitrary_service(client: DespatchBaySDK, config: Config):
    all_services = client.get_services()
    arbitrary_service = next((service for service in all_services if service.service_id == config.dbay['service']),
                             all_services[0])
    return arbitrary_service


def get_actual_service(config: Config, client: DespatchBaySDK, shipment: Shipment) -> Service:
    """
    requires a shipment request object to exist in given shipment
    returns the service specified in config.toml or first available
    marks shipment.default_service_matched
    """
    available_services = client.get_available_services(shipment.shipment_request)
    shipment.service_menu_map = ({service.name: service for service in available_services})
    available_service_match = next((a for a in available_services if a.service_id == config.dbay['service']), None)
    shipment.default_service_matched = True if available_service_match else False
    shipment.available_services = available_services

    return available_service_match if available_service_match else available_services[0]


def get_home_sender(client: DespatchBaySDK, config: Config) -> Sender:
    """ return a dbay sender object representing home address defined in toml / Shipper.config"""
    return client.sender(
        address_id=config.home_address['address_id'],
        name=config.home_address['contact'],
        email=config.home_address['email'],
        telephone=config.home_address['telephone'],
        sender_address=client.get_sender_addresses()[0].sender_address
    )


def get_home_recipient(client: DespatchBaySDK, config: Config) -> Recipient:
    """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
    return client.recipient(
        name=config.home_address['contact'],
        email=config.home_address['email'],
        telephone=config.home_address['telephone'],
        recipient_address=client.find_address(config.home_address['postal_code'],
                                              config.home_address['search_term'])
    )


def get_remote_sender(client: DespatchBaySDK, shipment: Shipment, remote_address: Address) -> Sender:
    return client.sender(
        name=shipment.contact,
        email=shipment.email,
        telephone=shipment.telephone,
        sender_address=remote_address)


def get_remote_recip(shipment: Shipment, client: DespatchBaySDK, remote_address: Address) -> Sender:
    return client.recipient(
        name=shipment.contact,
        email=shipment.email,
        telephone=shipment.telephone,
        recipient_address=remote_address)


def quick_match(client: DespatchBaySDK, shipment: Shipment, candidate_key_dict: dict):
    for add, key in candidate_key_dict.items():
        add = add.split(',')[0]

        if add == shipment.customer:
            return client.get_address_by_key(key)
        if add == shipment.str_to_match:
            return client.get_address_by_key(key)


def get_bestmatch(client: DespatchBaySDK, candidate_key_dict: dict, shipment: Shipment) -> BestMatch:
    """
    Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
    search by customer name, then shipment search_term
    call explicit_matches to compare strings,
    call get_bestmatch for fuzzy results,
    if best score exceed threshold ask user to confirm
    If still no valid address, call get_new_address.
    """
    fuzzyscores = []
    for address_str, key in candidate_key_dict.items():
        candidate_address = client.get_address_by_key(key)
        if explicit_match := get_explicit_bestmatch(candidate_address=candidate_address, shipment=shipment):
            return explicit_match
        else:
            fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
    else:
        # finished loop, no explicitmatch so get a bestmatch from fuzzyscores
        bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
        return bestmatch


def search_adddress(client: DespatchBaySDK, shipment: Shipment) -> Address | None:
    """ Return an address if found by simple search on postcode and building number or company name """
    try:
        address = client.find_address(shipment.postcode, shipment.customer)
    except ApiException as e1:
        try:
            address = client.find_address(shipment.postcode, shipment.search_term)
        except ApiException as e2:
            return None
    return address or None


def check_address_company(config: Config, address: Address, shipment: Shipment):
    """ see if the address has company name and whether that matches our records, popup to confirm if not"""

    if config.sandbox:
        # then all results are spurious and will not match
        return address

    if not address.company_name:
        return address
    elif address.company_name:
        if address.company_name == shipment.customer \
                or address.company_name in shipment.address_as_str:
            return address
        else:
            pop_msg = f'Address Company name and Shipment Customer do not match:\n' \
                      f'\nCustomer: {shipment.customer}\n' \
                      f'Address Company Name: {address.company_name})\n' \
                      f'{shipment.address_as_str}\n' \
                      f'\n[Yes] to accept matched address or [No] to edit or replace it'

        answer = sg.popup_yes_no(pop_msg, line_width=100)
        return address if answer == 'Yes' else None
        # self.compare_address_to_shipment(address=address, shipment=shipment)


def compare_address_to_shipment(config: Config, address: Address, shipment: Shipment):
    """ Gui compares address to shipment deliver details"""
    address_dict = dict(
        street=shipment.str_to_match,
        company_name=shipment.customer,
        postcode=shipment.postcode,
    )
    window = compare_addresses_window(config=config, address=address, address_dict=address_dict)
    e, v = window.read()
    while True:
        if sg.WIN_CLOSED in e:
            break
    window.close()


#
# def check_address_company(address: Address, shipment: Shipment):
#     if not address.company_name:
#         return address
#     elif address.company_name:
#         pop_msg = f'Address matched from direct search\n'
#         if address.company_name != shipment.customer:
#             pop_msg += f'But <Customer> ({shipment.customer}) and <Company> ({address.company_name}) do not match:\n'
#         if address.company_name in shipment.address_as_str:
#             pop_msg += f'\nHowever <Company Name> ({address.company_name} is in <address string> ({shipment.address_as_str})'
#         pop_msg += '\n[Yes] to accept matched address or [No] to fetch a new one'
#         answer = sg.popup_yes_no(pop_msg)
#         return address if answer == 'Yes' else None
#

def get_candidate_keys_dict(shipment: Shipment, client: DespatchBaySDK, postcode=None) -> dict:
    """ return a dict of dbay addresses and keys, from postcode or shipment.postcode,
        popup if postcode no good """
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

    available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.dbay['courier'])
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


def get_explicit_bestmatch(shipment: Shipment, candidate_address) -> BestMatch | None:
    """ compares shipment details to address, return a bestmatch if an explicit match is found  else None"""
    address_str_to_match = shipment.str_to_match
    if shipment.customer == candidate_address.company_name or \
            address_str_to_match == candidate_address.street:
        best_match = BestMatch(address=candidate_address, category='explicit', score=100,
                               str_matched=address_str_to_match)
        return best_match
    else:
        return None


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


def email_label():
    # todo this
    ...


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
    shipment_return = client.book_shipments(shipment_id)[0]
    shipment.collection_booked = True
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


def download_label(client: DespatchBaySDK, config: Config, shipment: Shipment):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name}.pdf at location specified in config.toml"""
    try:
        label_pdf:Document = client.get_labels(document_ids=shipment.shipment_return.shipment_document_id, label_layout='2A4')

        printable_shipment_name = re.sub(r'[:/\\|?*<">]', "_", shipment.shipment_name)
        label_string:str = printable_shipment_name + '.pdf'
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


def address_gui_from_address(address: Address, window: sg.Window):
    if address:
        address_dict = {k: v for k, v in vars(address).items() if 'soap' not in k}
        address_dict.pop('country_code', None)
        for k, v in address_dict.items():
            window[f'-ADDRESS_{k.upper()}-'].update(v or '')


def update_address_from_gui(config: Config, address: Address, values: dict):
    address_fields = config.address_fields
    for field in address_fields:
        value = values.get(f'-ADDRESS_{field.upper()}-', None)
        setattr(address, field, value)
    return address


def update_remote_address_from_gui(config: Config, values: dict):
    contact_fields = config.contact_fields
    for field in contact_fields:
        ...
        # value = values.get(address_frame_key)
        # if all([value, field]):
        #     setattr(address, field, value)


def update_contact_from_gui(config: Config, contact: Sender | Recipient, values: dict):
    contact_fields = config.contact_fields
    contact_type = type(contact).__name__
    for field in contact_fields:
        value = values.get(f'-{contact_type}_{field}-'.upper())
        if all([value, field]):
            setattr(contact, field, value)


def update_commence(config: Config, shipment: Shipment, id_to_pass: str):
    """ runs cmclibnet via powershell script to add shipment_id to commence db """

    ps_script = str(config.cmc_logger)
    try:  # utility class static method runs powershell script bypassing execuction policy
        commence_edit = Utility.powershell_runner(ps_script,
                                                  shipment.category, shipment.shipment_name, id_to_pass, str(shipment.is_return))
    except RuntimeError as e:
        sg.popup_scrolled(f'Unable to log to commence, Runtime error:\n{e}')
        shipment.logged_to_commence = False
    else:
        if commence_edit == 0:
            shipment.logged_to_commence = True
    return shipment.logged_to_commence


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


def check_today_ship(shipment):
    keep_shipment = True
    if shipment.send_out_date == datetime.today().date() and datetime.now().hour > 12:
        keep_shipment = True if sg.popup_ok_cancel(
            f"Warning - Shipment Send Out Date is today and it is afternoon\n"
            f"{shipment.shipment_name} will not be collected today.\n"
            "'Ok' to continue, 'Cancel' to remove shipment from manifest?") == 'Ok' else False
    return shipment if keep_shipment else None
