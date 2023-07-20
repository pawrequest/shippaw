from typing import Iterable

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException, RateLimitException
from fuzzywuzzy import fuzz

from gui.address_gui import AddressGui
from core.enums import BestMatch, FuzzyScores
from shipper.shipment import Shipment, parse_amherst_address_string
from core.config import logger




def address_from_searchterms(client: DespatchBaySDK, postcode:str, search_terms:Iterable) -> Address | None:

    check_set = set(search_terms)
    for term in check_set:
        try:
            logger.info(f"ADDRESS SEARCH: {postcode} & {term}")
            address = client.find_address(postcode, term)
            return address
        except ApiException as e1:
            if 'No Addresses Found At Postcode' in e1.args:
                logger.info(f"ADDRESS SEARCH FAIL - {str(e1)}")
            continue
    else:
        logger.info(f"ALL ADDRESS SEARCHES FAIL")
        sg.popup_quick_message("Address Not Matched - please check it")
        return None




def get_bestmatch(client: DespatchBaySDK, shipment: Shipment) -> BestMatch:
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
                or address.company_name in shipment._address_as_str \
                or address.company_name in shipment.delivery_name:
            return address
        else:
            pop_msg = f'Address Company name and Shipment Customer do not exactly match:\n' \
                      f'\nCustomer: {shipment.customer}\n' \
                      f'Address Company Name: {address.company_name}\n' \
                      f'\nShipment Delivery Details:\n{shipment.delivery_name} \n{shipment._address_as_str}\n' \
                      f'\n[Yes] to accept matched address or [No] to edit / replace'

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
            if postcode is None:
                break
            continue
        else:
            return candidate_keys_dict



def get_candidate_keys_new(client: DespatchBaySDK, postcode) -> dict:
    """ return a dict of dbay addresses and keys, from postcode or shipment.postcode,
        popup if postcode no good """
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



def address_from_logic(client: DespatchBaySDK, shipment: Shipment, sandbox:bool) -> Address | None:
    # if address := address_from_search(client=client, shipment=shipment):
    terms = {shipment.customer, shipment.delivery_name,
             parse_amherst_address_string(str_address=shipment._address_as_str)}

    if address := address_from_searchterms(client=client, postcode=shipment.postcode, search_terms=terms):
        if sandbox:
            # then nothing will match so give up now
            return address
        if checked_address := check_address_company(address=address, shipment=shipment):
            logger.info(f"Address Passed Company Name Check")
            return checked_address
    return None


def address_from_bestmatch(client, shipment):
    try:
        # shipment.candidate_keys = get_candidate_keys_dict(client=client, shipment=shipment)  # 1x api call
        shipment.candidate_keys = get_candidate_keys_new(client=client, postcode=shipment.postcode)
        shipment.bestmatch = get_bestmatch(client=client, shipment=shipment)  # candidate key x api call
        log_str = "\n".join(f"{key} : {value}" for key, value in shipment.candidate_keys.items())
        logger.info(f"CANDIDATE KEYS :\n{log_str}")
        logger.info(f"BESTMATCH : {shipment.bestmatch}")
    except RateLimitException:
        logger.info("API CALLS EXCEEDED ABANDONING SEARCH")
        return None
    return shipment.bestmatch.address


def address_from_gui(client, sandbox:bool, outbound:bool, shipment):
    address_gui = AddressGui(outbound=outbound, sandbox=sandbox, client=client, shipment=shipment, address=shipment.bestmatch.address,
                             contact=shipment.remote_contact)
    address_gui.get_address()
    address = address_gui.address
    logger.info(f'ADDRESS FROM GUI - {shipment.shipment_name_printable} - {address=}')
    return address
""" GET CONTACT?"""
