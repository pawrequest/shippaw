import logging
from typing import List

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException
from fuzzywuzzy import fuzz

from .shipment import ShipmentRequested
from ..core.entities import BestMatch, FuzzyScores, AddressMatch
from ..core.funcs import retry_with_backoff
from ..gui.keys_and_strings import ADDRESS_STRING

logger = logging.getLogger(__name__)

def fuzzy_address_script(shipment, client: DespatchBaySDK) -> Address:
    """ takes a client, shipment and candidate_keys dict, returns a fuzzy matched address"""
    fuzzyscores:List[FuzzyScores] = []
    logger.info({'Getting Fuzzy Address'})

    candidate_keys = retry_with_backoff(get_candidate_keys, backoff_in_seconds=60, postcode=shipment.postcode, client=client)
    for address_str, key in candidate_keys.items():
        candidate_address = retry_with_backoff(client.get_address_by_key, retries=5, backoff_in_seconds=60, key=key)
        if get_explicit_match(shipment=shipment, candidate_address=candidate_address):
            shipment.remote_address_matched = AddressMatch.EXPLICIT
            return candidate_address
        fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
    bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
    logger.info(f'Bestmatch Address: {bestmatch.address}')
    shipment.remote_address_matched = AddressMatch.FUZZY
    return bestmatch.address


def get_explicit_match(shipment: ShipmentRequested, candidate_address: Address) -> bool:
    """Compares various shipment details to address and returns the address if matched, else None."""
    if candidate_address.company_name and (
            shipment.customer in candidate_address.company_name or
            candidate_address.company_name in shipment.customer or
            shipment.delivery_name in candidate_address.company_name or
            candidate_address.company_name in shipment.delivery_name
    ):
        logger.info(f'Explicit Match Found: {ADDRESS_STRING(candidate_address)}')
        return True

    if shipment.str_to_match == candidate_address.street:
        return True

    return False


def get_fuzzy_scores(candidate_address, shipment) -> FuzzyScores:
    """" return a Fuzzyscores representing distance from shipment details to candidate_address"""
    logger.info(f'Getting Fuzzy Scores for {ADDRESS_STRING(candidate_address)}')
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

def pop_up_func():
    return sg.popup_get_text(f'Bad postcode - Try Again')

def get_candidate_keys(postcode, client: DespatchBaySDK, popup_func=pop_up_func) -> dict:
    """takes a client and postcode, returns a dict with keys= dbay addresses as strings and values =  dbay address keys"""
    candidate_keys_dict = None
    while not candidate_keys_dict:
        try:
            candidate_keys_dict = {candidate.address: candidate.key for candidate in
                                   client.get_address_keys_by_postcode(postcode)}
        except ApiException as e:
            if "postcode" in str(e).lower():
                postcode = popup_func()
                if postcode is None:
                    break
            continue
        else:
            return candidate_keys_dict
