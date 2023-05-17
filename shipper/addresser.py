import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException
from fuzzywuzzy import fuzz

from gui.address_gui import AddressGui
from core.enums import BestMatch, FuzzyScores
from shipper.shipment import Shipment
from core.config import get_amdesp_logger

logger = get_amdesp_logger()


def address_from_search(client: DespatchBaySDK, shipment: Shipment) -> Address | None:
    """ Return an address if found by simple search on postcode and building number or company name """
    try:
        return client.find_address(shipment.postcode, shipment.customer)
    except ApiException as e1:
        try:
            return client.find_address(shipment.postcode, shipment.delivery_name)
        except ApiException as e2:
            try:
                search_term = shipment.parse_amherst_address_string(str_address=shipment.str_to_match)
                return client.find_address(shipment.postcode, search_term)
            except ApiException as e3:
                return None




def get_bestmatch(client: DespatchBaySDK, shipment: Shipment) -> BestMatch:
    """
    requires shipment.candidate_keys dict
    Return a dbay recipient/sender object representing the customer address defined in imported xml or dbase file.
    search by customer name, then shipment search_term
    call explicit_matches to compare strings,
    call get_bestmatch for fuzzy results,
    if best score exceed threshold ask user to confirm
    If still no valid address, call get_new_address.
    """
    fuzzyscores = []
    for address_str, key in shipment.candidate_keys.items():
        candidate_address = client.get_address_by_key(key)
        if explicit_match := get_explicit_bestmatch(candidate_address=candidate_address, shipment=shipment):
            return explicit_match
        else:
            fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
    else:
        # finished loop, no explicitmatch from candidates so get a bestmatch from fuzzyscores
        bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
        return bestmatch


def get_explicit_bestmatch(shipment: Shipment, candidate_address) -> BestMatch | None:
    """ compares shipment details to address, return a bestmatch if an explicit match is found  else None"""

    if shipment.customer == candidate_address.company_name \
            or shipment.str_to_match == candidate_address.street \
            or shipment.delivery_name == candidate_address.company_name:
        return BestMatch(address=candidate_address, category='explicit', score=100,
                               str_matched=shipment.str_to_match)
    else:
        return None




def check_address_company(address: Address, shipment: Shipment) -> Address | None:
    """ compare address company_name to shipment [customer, address_as_str, delivery_name
    if no address.company_name insert shipment.delivery_name"""

    if not address.company_name:
        # address.company_name = shipment.delivery_name
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
    candidate_keys_dict = None
    while not candidate_keys_dict:
        try:
            candidate_keys_dict = {candidate.address: candidate.key for candidate in
                                   client.get_address_keys_by_postcode(postcode)}
        except ApiException as e:
            postcode = sg.popup_get_text(f'Bad postcode for {shipment.customer} - Please Enter')
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
    best_address = None
    best_score = 0
    best_category = ""
    str_matched = ''

    for f in fuzzyscores:
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

    return BestMatch(str_matched=str_matched, address=best_address, category=best_category, score=best_score)



def address_from_logic(client: DespatchBaySDK, shipment: Shipment) -> Address | None:
    """ returns an address, tries by direct search, quick address string comparison, explicit BestMatch, BestMatch from FuzzyScores, or finally user input  """
    if address := address_from_search(client=client, shipment=shipment):
        logger.info(f"Address Matched fom search: {address}")
        if checked_address := check_address_company(address=address, shipment=shipment):
            logger.info(f"Address Passed Company Name Check")
            return checked_address
    return None


def address_from_bestmatch(client, shipment):
    shipment.candidate_keys = get_candidate_keys_dict(client=client, shipment=shipment)  # 1x api call
    shipment.bestmatch = get_bestmatch(client=client, shipment=shipment)  # candidate key x api call
    logger.info(f"CANDIDATE KEYS : {shipment.candidate_keys}")
    logger.info(f"BESTMATCH : {shipment.bestmatch}")
    return shipment.bestmatch.address


def address_from_gui(client, config, shipment):
    address_gui = AddressGui(config=config, client=client, shipment=shipment, address=shipment.bestmatch.address,
                             contact=shipment.remote_contact)
    address_gui.get_address()
    address, contact = address_gui.address, address_gui.contact
    logger.info(f'ADDRESS FROM GUI - {shipment.shipment_name_printable} - {address=}')
    return address, contact
