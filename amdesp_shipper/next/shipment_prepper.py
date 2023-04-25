from datetime import datetime
from typing import List, Protocol

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address, CollectionDate, Parcel, Recipient, Sender, Service
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException
from fuzzywuzzy import fuzz

from amdesp_shipper.address_gui import AddressGui
from amdesp_shipper.config import Config, get_amdesp_logger
from amdesp_shipper.enums import BestMatch, Contact, DateTimeMasks, FuzzyScores, Job
from amdesp_shipper.shipment import Shipment

logger = get_amdesp_logger()


class Prepper(Protocol):
    def prep_shipments(self):
        """in child"""

    def get_remote_address(self, client: DespatchBaySDK, shipment: Shipment) -> Address:
        """in child"""


class JobProcessor:
    def __init__(self, jobs: List[Job]):
        self.jobs = jobs

    def list_processor(self):
        while self.jobs:
            this_job = self.jobs.pop()
            self.process_job(this_job)

    def process_job(self, job):
        if job.add:
            self.add_shipment()
        if job.book:
            self.book_shipment()
        if job.print_or_email:
            if job.outbound:
                self.print_label()
            if job.outbound is False:
                self.email_label()

    def add_shipment(self):
        ...

    def book_shipment(self):
        ...

    def email_label(self):
        ...

    def print_label(self):
        ...


class ShipmentListPrepper:
    def __init__(self, client: DespatchBaySDK, config: Config):
        self.client = client
        self.config = config
        self.outbound: bool = config.outbound
        self.home_address_dbay_key: str = config.home_address.dbay_key
        self.home_address_id: str = config.home_address.address_id
        self.home_contact = config.home_contact
        self.sandbox = config.sandbox

    def shipment_processor(self, shipments:[Shipment]):
        processed_shipments = [Shipment]

        while shipments:
            ship_in_play:Shipment = shipments.pop()
            processor = SingleProcessor(config=self.config, client=self.client)
            processed = processor.process_a_shipment(shipment=ship_in_play)
            job = Job(
                shipment_request=ship_in_play
            )
            # processed_shipment = self.process_a_shipment(ship_in_play)
            processed_shipments.append(processed)
        return processed_shipments


class SingleProcessor:
    def __init__(self, client: DespatchBaySDK, config: Config):
        self.client = client
        self.config = config
        self.outbound: bool = config.outbound
        self.home_address_dbay_key: str = config.home_address.dbay_key
        self.home_address_id: str = config.home_address.address_id
        self.home_contact = config.home_contact
        self.sandbox = config.sandbox

    def process_a_shipment(self, shipment):
        try:
            remote_contact = self.get_remote_contact(shipment)
            remote_address = self.get_remote_address(shipment=shipment)
            if not self.sandbox:  # nothing matches in sandbox land
                remote_address = self.check_address_company(address=remote_address, shipment=shipment)
                # remote_address = self.bestmatch_to_address_from_gui(bestmatch=remote_address, remote_contact=remote_address, shipment=shipment)

            self.get_sender_recip(remote_address, remote_contact, shipment)
            shipment.service = self.get_arbitrary_service()  # needed to get dates
            shipment.despatch_objects.collection_date = self.get_collection_date(shipment=shipment)
            check = self.check_today_ship(shipment)  # no bookings after 1pm
            if check is None:
                return None
            shipment.despatch_objects.parcels = self.get_parcels(num_parcels=shipment.boxes)
            shipment.despatch_objects.shipment_request = self.get_shipment_request(shipment=shipment)
            shipment.despatch_objects.service = self.get_actual_service(service_id=self.config.dbay_creds.service_id,
                                                                        shipment=shipment)
        except Exception as e:
            logger.exception(f'Error with {shipment.shipment_name_printable}:\n {e}')
        else:
            return shipment

    def get_sender_recip(self, remote_address, remote_contact, shipment):
        if self.outbound:
            shipment.despatch_objects.sender = self.client.sender(address_id=self.home_address_id)
            shipment.despatch_objects.recipient = self.get_remote_recipient(contact=remote_contact,
                                                                            remote_address=remote_address)
        else:
            shipment.despatch_objects.sender = self.get_remote_sender(contact=remote_contact,
                                                                      remote_address=remote_address)
            shipment.despatch_objects.recipient = self.get_home_recipient()

    def bestmatch_to_address_from_gui(self, bestmatch:BestMatch, remote_contact, shipment):
        address_gui = AddressGui(config=self.config, client=self.client, shipment=shipment, address=bestmatch.address,
                                 contact=remote_contact)
        bestmatch = address_gui.address_gui_loop()
        return bestmatch

    def get_remote_contact(self, shipment):
        remote_contact = Contact(email=shipment.email, telephone=shipment.telephone,
                                 name=shipment.contact_name)
        return remote_contact

    def get_remote_address(self,shipment: Shipment) -> Address | BestMatch:
        """ returns an address, tries by direct search, quick address string comparison, explicit BestMatch, BestMatch from FuzzyScores, or finally user input  """
        config = self.config
        client = self.client
        candidate_keys = None

        address = self.address_from_search(client=client, shipment=shipment)
        logger.info(f"SEARCH MATCHED ADDRESS : {address}") if address else None

        if not address:
            candidate_keys = self.get_candidate_keys_dict(client=client, shipment=shipment)
            address = self.address_from_quickmatch(shipment=shipment, candidate_key_dict=candidate_keys)
            logger.info(f"QUICKMATCH ADDRESS : {address}") if address else None

        if not address:
            bestmatch = self.get_bestmatch(client=client, candidate_key_dict=candidate_keys, shipment=shipment)
            logger.info(f"BESTMATCH : {bestmatch}") if bestmatch else None
            address = bestmatch.address

        #
        # if not address:
        #     candidate_keys = candidate_keys or self.get_candidate_keys_dict(client=client, shipment=shipment)
        #     bestmatch = self.get_bestmatch(candidate_key_dict=candidate_keys, shipment=shipment, client=client)
        #     logger.info(f"BESTMATCH FROM KEYS : {bestmatch}") if bestmatch else None
        #     return bestmatch

        return address

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
                contents=self.config.home_address['parcel_contents'],
                value=500,
                weight=6,
                length=60,
                width=40,
                height=40,
            )
            parcels.append(parcel)
        logger.info(f'PREPPING SHIPMENT - PARCELS {parcels}')

        return parcels

    ...

    def get_actual_service(self, service_id:str, shipment: Shipment) -> Service:
        """
        requires a shipment request object to exist in given shipment,
        flag shipment.default_service_matched
        return the service specified in config.toml or first available,
        """
        available_services = self.client.get_available_services(shipment.shipment_request)
        shipment.service_menu_map = ({service.name: service for service in available_services})
        available_service_match = next((a for a in available_services if a.service_id == service_id),
                                       None)
        shipment.default_service_matched = True if available_service_match else False
        shipment.available_services = available_services

        return available_service_match if available_service_match else available_services[0]

    def get_home_recipient(self) -> Recipient:
        """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
        address = self.client.get_address_by_key(self.home_address_dbay_key)
        home_contact_dict = self.home_contact
        return self.client.recipient(
            recipient_address=address, **home_contact_dict)

    def get_remote_sender(self, contact: Contact, remote_address: Address) -> Sender:
        sender = self.client.sender(
            sender_address=remote_address, **contact._asdict())
        return sender

    def get_remote_recipient(self, contact: Contact, remote_address: Address) -> Recipient:
        recip = self.client.recipient(
            recipient_address=remote_address, **contact._asdict())
        logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {recip}')
        return recip

    def address_from_search(self, client: DespatchBaySDK, shipment: Shipment) -> Address | None:
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

    def address_from_quickmatch(self,shipment: Shipment, candidate_key_dict: dict) -> Address | None:
        """ takes a compares Dbay address strings to shipment.customer and shipment.str_to_match"""
        for add, key in candidate_key_dict.items():
            add = add.split(',')[0]

            if add == shipment.customer:
                return self.client.get_address_by_key(key)
            if add == shipment.str_to_match:
                return self.client.get_address_by_key(key)
            else:
                return None

    def get_bestmatch(self, client: DespatchBaySDK, candidate_key_dict: dict, shipment: Shipment) -> BestMatch:
        """ tries to return an ExplicitBestMatch else creates a FuzzyScores object to return a BestMatch from"""
        fuzzyscores = []
        for address_str, key in candidate_key_dict.items():
            candidate_address = client.get_address_by_key(key)
            if explicit_match := self.get_explicit_bestmatch(candidate_address=candidate_address, shipment=shipment):
                return explicit_match
            else:
                fuzzyscores.append(self.get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
        else:
            # finished loop, no explicitmatch so get a bestmatch from fuzzyscores
            bestmatch = self.bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
            return bestmatch

    def get_explicit_bestmatch(self, shipment: Shipment, candidate_address) -> BestMatch | None:
        """ compares shipment details to address, return a bestmatch if an explicit match is found  else None"""

        address_str_to_match = shipment.str_to_match
        if shipment.customer == candidate_address.company_name or \
                address_str_to_match == candidate_address.street:
            best_match = BestMatch(address=candidate_address, category='explicit', score=100,
                                   str_matched=address_str_to_match)
            return best_match
        else:
            return None

    def check_address_company(self, address: Address, shipment: Shipment) -> Address | None:
        """ compare address company_name to shipment [customer, address_as_str, delivery_name
        if no address.company_name insert shipment.delivery_name"""

        if not address.company_name:
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

    def get_candidate_keys_dict(self, shipment: Shipment, client: DespatchBaySDK, postcode=None) -> dict:
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

    def get_shipment_request(self, shipment: Shipment):
        """ returns a dbay shipment request object from shipment"""
        request = self.client.shipment_request(
            service_id=shipment.despatch_objects.service.service_id,
            parcels=shipment.despatch_objects.parcels,
            client_reference=shipment.customer,
            collection_date=shipment.despatch_objects.collection_date,
            sender_address=shipment.despatch_objects.sender,
            recipient_address=shipment.despatch_objects.recipient,
            follow_shipment=True
        )

        logger.info(f'PREPPING SHIPMENT - SHIPMENT REQUEST {request}')
        return request

    def get_fuzzy_scores(self, candidate_address, shipment) -> FuzzyScores:
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

    def bestmatch_from_fuzzyscores(self, fuzzyscores: [FuzzyScores]) -> BestMatch:
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

    def check_today_ship(self, shipment):
        keep_shipment = True
        if shipment.send_out_date == datetime.today().date() and datetime.now().hour > 12:
            keep_shipment = True if sg.popup_ok_cancel(
                f"Warning - Shipment Send Out Date is today and it is afternoon\n"
                f"{shipment.shipment_name_printable} would be collected on {datetime.strptime(shipment.despatch_objects.collection_date.date, DateTimeMasks.DB.value):{DateTimeMasks.DISPLAY.value}}.\n"
                "'Ok' to continue, 'Cancel' to remove shipment from manifest?") == 'Ok' else False

        logger.info(f'PREP SHIPMENT - CHECK TODAY SHIP {shipment.send_out_date}')
        return shipment if keep_shipment else None
