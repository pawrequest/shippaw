import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import PySimpleGUI as sg
import dotenv
import win32com.client
from fuzzywuzzy import fuzz

from amdesp_shipper.address_gui import AddressGui
from amdesp_shipper.config import Config
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.documents_client import Document
from despatchbay.exceptions import ApiException

from amdesp_shipper.enums import BestMatch, Contact, DateTimeMasks, FieldsList, FuzzyScores, Job
from amdesp_shipper.main_gui import MainGui
from amdesp_shipper.shipment import Shipment
from amdesp_shipper.config import get_amdesp_logger
from amdesp_shipper.tracking_gui import tracking_loop

dotenv.load_dotenv()
logger = get_amdesp_logger()
LIMITED_SHIPMENTS = 1


class Shipper:
    def __init__(self, config: Config, client: DespatchBaySDK, gui: MainGui, shipments: [Shipment]):
        self.shipment_to_edit: Optional[Shipment] = None
        self.gui = gui
        self.config = config
        self.shipments: [Shipment] = shipments
        self.client = client

    def dispatch(self):
        mode = self.config.mode
        try:
            if 'ship' in mode:
                prepped_shipments = self.prep_shipments()
                booked_shipments = self.main_gui_loop(prepped_shipments)
                self.gui.post_book(shipments=booked_shipments)

            elif 'track' in mode:
                for shipment in self.shipments:
                    if any([shipment.outbound_id, shipment.inbound_id]):
                        result = tracking_loop(self.gui, shipment=shipment)
            else:
                raise ValueError('Ship Mode Fault')
        except Exception as e:
            logger.exception(f'DISPATCH EXCEPTION \n{e}')

        if sg.popup_yes_no("Restart? No to close") == 'Yes':
            self.dispatch()
        else:
            sys.exit()

    def prep_shipments(self):
        """  gets sender, recipient, service, date, parcels and shipment request objects from dbay api \n
        stores all in shipment attrs
        uses an arbitrary service to get collection dates, then gets real service from eventual shipment_return dbay object"""
        logger.info('PREP SHIPMENTS')
        # shipments = shipments[0:LIMITED_SHIPMENTS] if LIMITED_SHIPMENTS else shipments
        prepped_shipments = []
        config = self.config
        client = self.client

        # get a dbay object representing home base for either sender or receiver as per config.outbound
        home_sender_recip = (get_home_sender(client=client, config=config) if config.outbound
                             else get_home_recipient(client=client, config=config))
        logger.info(f'PREP SHIPMENT -  {home_sender_recip=}')

        for shipment in self.shipments:
            try:
                shipment.remote_contact = Contact(email=shipment.email, telephone=shipment.telephone,
                                                  name=shipment.contact_name)
                self.get_sender_recip(home_sender_recip=home_sender_recip, shipment=shipment)
                shipment.service = self.get_arbitrary_service()  # needed to get dates
                shipment = check_today_ship(shipment)  # no bookings after 1pm
                if shipment is None:
                    continue
                shipment.collection_date = self.get_collection_date(shipment=shipment)
                shipment.parcels = self.get_parcels(num_parcels=shipment.boxes)
                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)
                shipment.service = get_actual_service(client=client, config=config, shipment=shipment)

                prepped_shipments.append(shipment)

            except Exception as e:
                self.shipments.remove(shipment)
                logger.exception(f'Error with {shipment.shipment_name_printable}:\n {e}')
                continue

        return prepped_shipments


    def main_gui_loop(self, shipments: [Shipment]):
        """ pysimplegui main_loop, takes a prebuilt window and shipment list,
        listens for user input and updates shipments
        listens for go_ship  button to start booking"""
        logger.info('GUI LOOP')

        self.gui.window = self.gui.bulk_shipper_window(shipments=shipments)

        while True:
            self.gui.event, self.gui.values = self.gui.window.read()
            if self.gui.event == sg.WIN_CLOSED:
                self.gui.window.close()
                sys.exit()

            elif self.gui.event == '-GO_SHIP-':
                if sg.popup_yes_no('Queue and book the batch?') == 'Yes':
                    sg.popup_quick_message('Please Wait')
                    # if booked := self.do_jobs():

                    if booked_ship := self.queue_and_book():
                        self.gui.window.close()
                        return booked_ship
            else:
                self.edit_shipment(shipments=shipments)
    # def do_jobs(self):
    #     job = Job()

    def edit_shipment(self, shipments):
        self.shipment_to_edit: Shipment = next((shipment for shipment in shipments
                                                if shipment.shipment_name_printable.lower() in self.gui.event.lower()))
        if 'boxes' in self.gui.event.lower():
            self.boxes_click()
        if 'service' in self.gui.event.lower():
            self.service_click()
        elif 'date' in self.gui.event.lower():
            self.date_click()
        elif 'sender' in self.gui.event.lower():
            self.sender_click()
        elif 'recipient' in self.gui.event.lower():
            self.recipient_click()
        elif 'remove' in self.gui.event.lower():
            shipments, self.gui.window = self.remove_click(shipments=shipments)

    def boxes_click(self):
        shipment_to_edit = self.shipment_to_edit
        event = self.gui.event
        window = self.gui.window
        if new_boxes := self.get_new_parcels(location=window.mouse_location()):
            shipment_to_edit.parcels = new_boxes
            window[event].update(f'{len(shipment_to_edit.parcels)}')
            window[f'-{shipment_to_edit.shipment_name_printable}_SERVICE-'.upper()].update(
                f'{shipment_to_edit.service.name} \n£{len(new_boxes) * shipment_to_edit.service.cost}')

    def remove_click(self, shipments: [Shipment]):
        shipments = [s for s in shipments if s != self.shipment_to_edit]
        self.gui.window.close()
        window = self.gui.bulk_shipper_window(shipments=shipments)
        return shipments, window

    def recipient_click(self):
        contact = self.shipment_to_edit.remote_contact if self.config.outbound else self.config.home_contact
        old_address = self.shipment_to_edit.recipient.recipient_address
        address_window = AddressGui(config=self.config, client=self.client, shipment=self.shipment_to_edit,
                                    address=old_address, contact=contact)
        new_address = address_window.address_gui_loop()
        self.shipment_to_edit.recipient.recipient_address = new_address
        self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=new_address))
        ...

    def date_click(self):
        new_collection_date = self.gui.new_date_selector(shipment=self.shipment_to_edit,
                                                         location=self.gui.window.mouse_location())
        self.gui.window[self.gui.event].update(self.gui.get_date_label(collection_date=new_collection_date))
        self.shipment_to_edit.collection_date = new_collection_date

    def sender_click(self):
        contact = self.config.home_contact if self.config.outbound else self.shipment_to_edit.remote_contact
        old_address = self.shipment_to_edit.sender.sender_address

        address_window = AddressGui(config=self.config, client=self.client, shipment=self.shipment_to_edit,
                                    contact=contact, address=old_address)
        new_address = address_window.address_gui_loop()
        if not new_address:
            return
        self.shipment_to_edit.sender.sender_address = new_address
        self.gui.window[self.gui.event].update(self.gui.get_address_button_string(address=new_address))

    def service_click(self):
        shipment_to_edit = self.shipment_to_edit
        new_service = self.gui.new_service_selector(default_service=shipment_to_edit.service.name,
                                                    menu_map=shipment_to_edit.service_menu_map,
                                                    location=self.gui.window.mouse_location())
        shipment_to_edit.service = new_service
        self.gui.window[self.gui.event].update(
            self.gui.get_service_string(service=new_service, num_boxes=len(shipment_to_edit.parcels)))

    def get_new_parcels(self, location):
        window = self.gui.get_new_parcels_window(location=location)
        e, v = window.read()
        if e == sg.WIN_CLOSED:
            window.close()
        if e == 'BOX':
            new_boxes = v[e]
            window.close()
            if parcels := self.get_parcels(int(new_boxes)):
                return parcels

    def queue_and_book(self):
        config = self.config
        client = self.client
        booked_shipments = []

        for shipment in self.shipments:
            try:
                shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
                shipment.shipment_request = get_shipment_request(client=client, shipment=shipment)

                shipment_id = client.add_shipment(shipment.shipment_request)
                setattr(shipment, f'{"outbound_id" if config.outbound else "inbound_id"}', shipment_id)

                shipment.shipment_return = book_shipment(client=client, shipment_id=shipment_id)

                download_label(client=client, config=config, shipment=shipment)

                if config.outbound:
                    print_label(shipment=shipment)
                else:
                    if sg.popup_yes_no(f'Email Label to {shipment.email}?') == 'Yes':
                        email_label(recipient=shipment.email, body=config.return_label_email_body,
                                    attachment=shipment.label_location)

                update_commence(config=config, shipment=shipment, id_to_pass=shipment_id)
                booked_shipments.append(shipment)
                log_shipment(config=config, shipment=shipment)
                continue

            except ApiException as e:
                sg.popup_error(f"Unable to Book {shipment.shipment_name_printable}\n"
                               f"\nServer returned the following error:\n"
                               f"{e}\n"
                               f"\nThat probably didn't help?\n"
                               f"How about this?:\n"
                               f"Available balance = £{client.get_account_balance().available}\n")
                continue
            except Exception as e:
                logger.exception(e)

        return booked_shipments if booked_shipments else None

    # def post_book(self, shipments: [Shipment]):
    #     headers = []
    #     frame = self.gui.booked_shipments_frame(shipments=shipments)
    #     window2 = sg.Window('Booking Results:', layout=[[frame]])
    #     while True:
    #         e2, v2 = window2.read()
    #         if e2 in [sg.WIN_CLOSED, 'Exit']:
    #             window2.close()
    #
    #         window2.close()
    #         break

    def get_remote_address(self, client: DespatchBaySDK, shipment: Shipment) -> Address:
        """ returns an address, tries by direct search, quick address string comparison, explicit BestMatch, BestMatch from FuzzyScores, or finally user input  """
        config = self.config
        candidate_keys = None

        address = address_from_search(client=client, shipment=shipment)
        logger.info(f"SEARCH MATCHED ADDRESS : {address}") if address else None

        if not address:
            candidate_keys = get_candidate_keys_dict(client=client, shipment=shipment)
            address = address_from_quickmatch(shipment=shipment, client=client, candidate_key_dict=candidate_keys)
            logger.info(f"QUICKMATCH ADDRESS : {address}") if address else None

        if not address:
            bestmatch = get_bestmatch(client=client, candidate_key_dict=candidate_keys, shipment=shipment)
            logger.info(f"BESTMATCH : {bestmatch}") if bestmatch else None
            address = bestmatch.address

        if address:
            if not config.sandbox:
                address = check_address_company(address=address, shipment=shipment)
            logger.info(f'CHECK ADDRESS COMPANY : {address if address else ""}')

        if not address:
            candidate_keys = candidate_keys or get_candidate_keys_dict(client=client, shipment=shipment)
            bestmatch = get_bestmatch(candidate_key_dict=candidate_keys, shipment=shipment, client=client)
            logger.info(f"BESTMATCH FROM KEYS : {bestmatch}") if bestmatch else None
            address_gui = AddressGui(config=config, client=client, shipment=shipment, address=bestmatch.address,
                                     contact=shipment.remote_contact)
            address = address_gui.address_gui_loop()

            logger.info(f'PREP GET REMOTE ADDRESS - {shipment.shipment_name_printable} - {address=}')

        return address

    def get_sender_recip(self, shipment: Shipment, home_sender_recip: Sender | Recipient):
        client = self.client
        config = self.config
        remote_address = self.get_remote_address(shipment=shipment, client=client)

        if config.outbound:
            shipment.sender = home_sender_recip
            shipment.recipient = get_remote_recipient(client=client, remote_address=remote_address,
                                                      contact=shipment.remote_contact)
        else:
            shipment.sender = get_remote_sender(client=client,
                                                remote_address=remote_address,
                                                contact=shipment.remote_contact)
            shipment.recipient = home_sender_recip

    def get_collection_date(self, shipment: Shipment) -> CollectionDate:
        """ return despatchbay CollecitonDate Entity
        make a menu_map of displayable dates to colleciton_date objects to populate gui choosers"""
        available_dates = self.client.get_available_collection_dates(sender_address=shipment.sender,
                                                                     courier_id=self.config.dbay_creds.courier)
        collection_date = None

        for potential_collection_date in available_dates:
            real_date = datetime.strptime(potential_collection_date.date, DateTimeMasks.DB.value)
            display_date = real_date.strftime(DateTimeMasks.DISPLAY.value)
            shipment.date_menu_map.update({display_date: potential_collection_date})
            if real_date == shipment.send_out_date:
                collection_date = potential_collection_date
                shipment.date_matched = True

        collection_date = collection_date or available_dates[0]

        logger.info(f'PREPPING SHIPMENT - COLLECTION DATE {collection_date}')
        return collection_date

    def get_arbitrary_service(self) -> Service:
        """ needed to get available dates, swapped out for real service later """
        client = self.client
        config = self.config
        all_services: [Service] = client.get_services()
        arbitrary_service: Service = next(
            (service for service in all_services if service.service_id == config.dbay_creds.service_id),
            all_services[0])
        logger.info(f'PREP SHIPMENT - ARBITRARY SERVICE {arbitrary_service.name}')

        return arbitrary_service

    def get_parcels(self, num_parcels: int) -> list[Parcel]:
        """ return an array of dbay parcel objects equal to the number of boxes provided
            uses arbitrary sizes because dbay api wont allow skipping even though website does"""
        parcels = []
        for x in range(num_parcels):
            parcel = self.client.parcel(
                contents=self.config.parcel_contents,
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            parcels.append(parcel)
        logger.info(f'PREPPING SHIPMENT - PARCELS {parcels}')

        return parcels


def get_actual_service(config: Config, client: DespatchBaySDK, shipment: Shipment) -> Service:
    """
    requires a shipment request object to exist in given shipment,
    flag shipment.default_service_matched
    return the service specified in config.toml or first available,
    """
    available_services = client.get_available_services(shipment.shipment_request)
    shipment.service_menu_map = ({service.name: service for service in available_services})
    available_service_match = next((a for a in available_services if a.service_id == config.dbay_creds.service_id),
                                   None)
    shipment.default_service_matched = True if available_service_match else False
    shipment.available_services = available_services

    return available_service_match if available_service_match else available_services[0]


# Dbay sender / recipient object getters
def get_home_sender(client: DespatchBaySDK, config: Config) -> Sender:
    """ return a dbay sender object representing home address defined in toml / Shipper.config"""
    return client.sender(address_id=config.home_address.address_id)


def get_home_recipient(client: DespatchBaySDK, config: Config) -> Recipient:
    """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
    address = client.get_address_by_key(config.home_address.dbay_key)
    return client.recipient(
        recipient_address=address, **config.home_contact._asdict())


def get_remote_sender(client: DespatchBaySDK, contact: Contact,
                      remote_address: Address) -> Sender:
    sender = client.sender(
        sender_address=remote_address, **contact._asdict())
    return sender


def get_remote_recipient(contact: Contact, client: DespatchBaySDK, remote_address: Address) -> Sender:
    recip = client.recipient(
        recipient_address=remote_address, **contact._asdict())
    logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {recip}')
    return recip


def address_from_search(client: DespatchBaySDK, shipment: Shipment) -> Address | None:
    """ Return an address if found by simple search on postcode and building number or company name """
    try:
        address = client.find_address(shipment.postcode, shipment.customer)
    except ApiException as e1:
        try:
            address = client.find_address(shipment.postcode, shipment.delivery_name)
        except ApiException as e2:
            try:
                search_term = shipment.parse_amherst_address_string(str_address=shipment.str_to_match)
                address = client.find_address(shipment.postcode, search_term)
            except ApiException as e3:
                return None
    return address or None


def address_from_quickmatch(client: DespatchBaySDK, shipment: Shipment, candidate_key_dict: dict):
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


def check_address_company(address: Address, shipment: Shipment) -> Address | None:
    """ compare address company_name to shipment [customer, address_as_str, delivery_name
    if no address.company_name insert shipment.delivery_name"""

    if not address.company_name:
        address.company_name = shipment.delivery_name
        return address
    elif address.company_name:
        if address.company_name == shipment.customer \
                or address.company_name in shipment.address_as_str \
                or address.company_name in shipment.delivery_name:
            return address
        else:
            pop_msg = f'Address Company name and Shipment Customer do not match:\n' \
                      f'\nCustomer: {shipment.customer}\n' \
                      f'Address Company Name: {address.company_name})\n' \
                      f'{shipment.address_as_str}\n' \
                      f'\n[Yes] to accept matched address or [No] to edit or replace it'

        answer = sg.popup_yes_no(pop_msg, line_width=100)
        return address if answer == 'Yes' else None


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
    request = client.shipment_request(
        service_id=shipment.service.service_id,
        parcels=shipment.parcels,
        client_reference=shipment.customer,
        collection_date=shipment.collection_date,
        sender_address=shipment.sender,
        recipient_address=shipment.recipient,
        follow_shipment=True
    )

    logger.info(f'PREPPING SHIPMENT - SHIPMENT REQUEST {request}')
    return request


# def get_dates_menu(client: DespatchBaySDK, config: Config, shipment: Shipment) -> dict:
#     """ get available collection dates as dbay collection date objects for shipment.sender.address
#         construct a menu_def for a combo-box
#         if desired send-date matches an available date then select it as default, otherwise select soonest colelction
#         return a dict with values and default_value"""
#
#     # potential dates as dbay objs not proper datetime objs
#     available_dates = client.get_available_collection_dates(shipment.sender.sender_address, config.courier_id)
#     datetime_mask = config.datetime_masks.display
#
#     chosen_collection_date_dbay = next((date for date in available_dates if parse(date.date) == shipment.date),
#                                        available_dates[0])
#
#     chosen_date_hr = f'{parse(chosen_collection_date_dbay.date):{datetime_mask}}'
#     shipment.date_menu_map.update({f'{parse(date.date):{datetime_mask}}': date for date in available_dates})
#     men_def = [f'{parse(date.date):{datetime_mask}}' for date in available_dates]
#
#     shipment.date = chosen_collection_date_dbay
#     return {'default_value': chosen_date_hr, 'values': men_def}
#

def get_fuzzy_scores(candidate_address, shipment) -> FuzzyScores:
    """" return a fuzzyscopres tuple"""
    address_str_to_match = shipment.str_to_match

    str_to_company = fuzz.partial_ratio(address_str_to_match, candidate_address.company_name)
    customer_to_company = fuzz.partial_ratio(shipment.customer, candidate_address.company_name)
    str_to_street = fuzz.partial_ratio(address_str_to_match, candidate_address.street)

    fuzzy_scores = FuzzyScores(
        address=candidate_address,
        str_matched=address_str_to_match,
        customer_to_company=customer_to_company,
        str_to_company=str_to_company,
        str_to_street=str_to_street)

    return fuzzy_scores


def bestmatch_from_fuzzyscores(fuzzyscores: [FuzzyScores]) -> BestMatch:
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
            # well we won't beat that?
            break

    best_match = BestMatch(str_matched=str_matched, address=best_address, category=best_category, score=best_score)

    return best_match


def email_label(recipient: str, body: str, attachment: Path):
    ol = win32com.client.Dispatch('Outlook.Application')
    newmail = ol.CreateItem(0)

    newmail.Subject = 'Radio Return - Shipping Label Attached'
    newmail.To = recipient
    newmail.Body = body
    attach = str(attachment)

    newmail.Attachments.Add(attach)
    newmail.Display()  # preview
    # newmail.Send()


#
# def email_label(shipment:Shipment):
#     ol = win32com.client.Dispatch('Outlook.Application')
#     newmail = ol.CreateItem(0)
#
#     newmail.Subject = 'Radio Return - Shipping Label Attached'
#     newmail.To = shipment.email
#     newmail.Body = 'Thanks for hiring from Amherst. Please find a pdf shipment label attached'
#     attach = str(shipment.label_location)
#
#     newmail.Attachments.Add(attach)
#     # newmail.Display()  # preview
#     newmail.Send()
#

# def get_parcels(num_parcels: int, client: DespatchBaySDK, config: Config) -> list[Parcel]:
#     """ return an array of dbay parcel objects equal to the number of boxes provided
#         uses arbitrary sizes because dbay api wont allow skipping even though website does"""
#     parcels = []
#     for x in range(num_parcels):
#         parcel = client.parcel(
#             contents=config.home_address['parcel_contents'],
#             value=500,
#             weight=6,
#             length=60,
#             width=40,
#             height=40,
#         )
#         parcels.append(parcel)
#     logger.info(f'PREPPING SHIPMENT - PARCELS {parcels}')
#
#     return parcels
#

def book_shipment(client: DespatchBaySDK, shipment_id: str):
    shipment_return = client.book_shipments(shipment_id)[0]
    # shipment.collection_booked = True
    return shipment_return


def download_label(client: DespatchBaySDK, config: Config, shipment: Shipment):
    """" downlaods labels for given dbay shipment_return object and stores as {shipment_name_printable}.pdf at location specified in config.toml"""
    try:
        label_pdf: Document = client.get_labels(document_ids=shipment.shipment_return.shipment_document_id,
                                                label_layout='2A4')

        label_string: str = shipment.shipment_name_printable + '.pdf'
        shipment.label_location = config.paths.labels / label_string
        label_pdf.download(shipment.label_location)
    except:
        return False
    else:
        return True


def powershell_runner(script_path: str, *params: str):
    POWERSHELL_PATH = "powershell.exe"

    commandline_options = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', script_path]
    for param in params:
        commandline_options.append("'" + param + "'")
    logger.info(f'POWERSHELL RUNNER - COMMANDS: {commandline_options}')
    process_result = subprocess.run(commandline_options, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True)
    logger.info(f'POWERSHELL RUNNER - PROCESS RESULT: {process_result}')
    if process_result.stderr:
        if r"Vovin.CmcLibNet\Vovin.CmcLibNet.dll' because it does not exist." in process_result.stderr:
            raise RuntimeError('CmCLibNet is not installed')
        else:
            raise RuntimeError(f'Std Error = {process_result.stderr}')
    else:
        return process_result.returncode


def update_commence(config: Config, shipment: Shipment, id_to_pass: str):
    """ runs cmclibnet via powershell script to add shipment_id to commence db """

    ps_script = str(config.paths.cmc_logger)
    try:  # utility class static method runs powershell script bypassing execuction policy
        commence_edit = powershell_runner(ps_script, shipment.category, shipment.shipment_name, id_to_pass,
                                          str(not config.outbound))
    except RuntimeError as e:
        logger.exception('Error logging to commence')
        sg.popup_scrolled(f'Error logging to commence - is it running?')
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

    for field in FieldsList.export.value:
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

    with open(config.paths.log_json, 'a') as f:
        # todo better loggging.... sqlite?
        json.dump(export_dict, f, sort_keys=True)
        f.write(",\n")


def check_today_ship(shipment):
    keep_shipment = True
    if shipment.send_out_date == datetime.today().date() and datetime.now().hour > 12:
        keep_shipment = True if sg.popup_ok_cancel(
            f"Warning - Shipment Send Out Date is today and it is afternoon\n"
            f"{shipment.shipment_name_printable} would be collected on {datetime.strptime(shipment.collection_date.date, DateTimeMasks.DB.value):{DateTimeMasks.DISPLAY.value}}.\n"
            "'Ok' to continue, 'Cancel' to remove shipment from manifest?") == 'Ok' else False

    logger.info(f'PREP SHIPMENT - CHECK TODAY SHIP {shipment.send_out_date}')
    return shipment if keep_shipment else None
