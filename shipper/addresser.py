from typing import Iterable

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address, Recipient, Sender
from despatchbay.exceptions import ApiException
from fuzzywuzzy import fuzz

import shipper.shipper
from core.config import Config, logger
from core.enums import BestMatch, Contact, FuzzyScores
from core.funcs import retry_with_backoff
from gui.address_gui import address_from_gui
from shipper.shipment import ShipmentInput, ShipmentRequested


def remote_address_script(shipment: ShipmentInput, remote_contact: Contact) -> (Address | bool):
    terms = {shipment.customer, shipment.delivery_name, shipment.str_to_match}

    if address := address_from_direct_search(postcode=shipment.postcode, search_terms=terms):
        return address

    logger.info({'No Explicit Match Found - getting fuzzy'})
    fuzzy = fuzzy_address(shipment=shipment)
    while True:
        address = address_from_gui(shipment=shipment, address=fuzzy, contact=remote_contact)
        if address is None:
            if sg.popup_yes_no(
                    f"If you don't enter an address the shipment for {shipment.customer_printable} will be skipped. \n'Yes' to skip, 'No' to try again") == 'Yes':
                return False
            continue
        else:
            return address


def address_from_direct_search(postcode: str, search_terms: Iterable) -> Address | None:
    client = shipper.shipper.DESP_CLIENT
    check_set = set(search_terms)
    for term in check_set:
        try:
            logger.info(f"ADDRESS SEARCH: {postcode} & {term}")
            address = client.find_address(postcode, term)
            return address
        except ApiException as e1:
            if 'No Addresses Found At Postcode' in e1.args:
                logger.info(f"ADDRESS SEARCH FAIL - {f'{postcode} + {term}'}")
            continue
    else:
        logger.info(f"ALL ADDRESS SEARCHES FAIL - {f'{postcode=}, {check_set=}'}")
        sg.popup_quick_message("Address Not Matched - please check it and consider updating Commence")
        return None


def get_explicit_match(shipment: ShipmentRequested, candidate_address: Address) -> bool:
    """Compares various shipment details to address and returns the address if matched, else None."""
    if candidate_address.company_name and (
            shipment.customer in candidate_address.company_name or
            candidate_address.company_name in shipment.customer or
            shipment.delivery_name in candidate_address.company_name or
            candidate_address.company_name in shipment.delivery_name
    ):
        return True

    if shipment.str_to_match == candidate_address.street:
        return True

    return False


def check_address_company(address: Address, shipment: ShipmentRequested) -> Address | None:
    """compares address.company_name to shipment [customer, address_as_str, delivery_name]"""

    if not address.company_name:
        logger.info(f'No company name at address - passing check')
        return address

    if address.company_name == shipment.customer \
            or address.company_name in shipment.address_as_str \
            or address.company_name in shipment.delivery_name:
        logger.info(f'Address company name matches customer')
        return address

    else:
        pop_msg = f'Company name @Found Address and Shipment Customer Name do not exactly match' \
                  f'\n\nDatabase Details:' \
                  f'\nCustomer = {shipment.customer}' \
                  f'\nDelivery Name= {shipment.delivery_name}' \
                  f'\nString Address from database=' \
                  f'\n{shipment.address_as_str}' \
                  f'\n\nFound Address Details:' \
                  f'\nAddress Company Name= {address.company_name}' \
                  f'\nStreet address= {address.street}' \
                  f'\n\n[Yes] to accept matched address or [No] to edit / replace'

        answer = sg.popup_yes_no(pop_msg, line_width=100)
        return address if answer == 'Yes' else None


def get_candidate_keys(postcode) -> dict:
    """takes a client and postcode, returns a dict with keys= dbay addresses as strings and values =  dbay address keys"""
    client = shipper.shipper.DESP_CLIENT
    candidate_keys_dict = None
    while not candidate_keys_dict:
        try:
            candidate_keys_dict = {candidate.address: candidate.key for candidate in
                                   client.get_address_keys_by_postcode(postcode)}
        except ApiException as e:
            if "postcode" in str(e).lower():
                postcode = sg.popup_get_text(f'Bad postcode - Try Again')
                if postcode is None:
                    break
            continue
        else:
            return candidate_keys_dict


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
    """ return BestMatch from a list of FuzzyScores"""
    logger.info(f'Searching BestMatch from fuzzyscores')
    best_address = None
    best_score = 0
    best_category = ""
    str_matched = ''

    for f in fuzzyscores:
        max_category = max(f.scores, key=lambda x: f.scores[x])
        max_score = f.scores[max_category]

        if max_score > best_score:
            logger.info(f'New BestMatch found with matchscore = {max_score}: {f.address}')
            best_score = max_score
            best_category = max_category
            best_address = f.address
            str_matched = f.str_matched
        if max_score == 100:
            logger.info(f'BestMatch found with score of 100: {f.address}')
            # well we won't beat that?
            break

    return BestMatch(str_matched=str_matched, address=best_address, category=best_category, score=best_score)


def fuzzy_address(shipment) -> Address:
    """ takes a client, shipment and candidate_keys dict, returns a fuzzy matched address"""
    client = shipper.shipper.DESP_CLIENT
    candidate_keys = get_candidate_keys(postcode=shipment.postcode)
    fuzzyscores = []
    for address_str, key in candidate_keys.items():
        candidate_address = retry_with_backoff(client.get_address_by_key, retries=5, backoff_in_seconds=60, key=key)
        if get_explicit_match(shipment=shipment, candidate_address=candidate_address):
            return candidate_address
        logger.info(f"{candidate_address=}")
        fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
    bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
    logger.info(f'Bestmatch Address: {bestmatch.address}')
    return bestmatch.address


def sender_from_address_id(address_id: str) -> Sender:
    """ return a dbay sender object representing home address defined in toml / Shipper.config"""
    client = shipper.shipper.DESP_CLIENT
    return client.sender(address_id=address_id)


def get_home_recipient(config: Config) -> Recipient:
    """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
    client = shipper.shipper.DESP_CLIENT
    address = client.get_address_by_key(config.home_address.dbay_key)
    return client.recipient(
        recipient_address=address, **config.home_contact.__dict__)


def recip_from_contact_and_key(dbay_key: str, contact: Contact) -> Recipient:
    """ return a dbay recipient object"""
    client = shipper.shipper.DESP_CLIENT
    return client.recipient(recipient_address=client.get_address_by_key(dbay_key), **contact.__dict__)


def sender_from_contact_address(contact: Contact,
                                remote_address: Address) -> Sender:
    client = shipper.shipper.DESP_CLIENT
    sender = client.sender(
        sender_address=remote_address, **contact.__dict__)
    return sender


def get_remote_recipient(contact: Contact, remote_address: Address) -> Sender:
    client = shipper.shipper.DESP_CLIENT
    recip = client.recipient(
        # recipient_address=remote_address, **contact._asdict())
        recipient_address=remote_address, **contact.__dict__)
    return recip


def recip_from_contact_address(contact: Contact, address: Address) -> Sender:
    client = shipper.shipper.DESP_CLIENT
    recip = client.recipient(
        # recipient_address=remote_address, **contact._asdict())
        recipient_address=address, **contact.__dict__)
    return recip


def get_home_sender_recip(home_contact, home_address, outbound) -> Sender | Recipient:
    """returns a sender object from home_address_id or recipient from home_address.dbay_key representing """
    client = shipper.shipper.DESP_CLIENT
    return client.sender(address_id=home_address.address_id) if outbound \
        else recip_from_contact_and_key(dbay_key=home_address.dbay_key,
                                        contact=home_contact)
