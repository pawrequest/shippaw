from typing import Iterable

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address, Sender, Recipient
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException, RateLimitException
from fuzzywuzzy import fuzz

from core.config import logger, Config
from core.enums import BestMatch, FuzzyScores, Contact
from core.funcs import retry_with_backoff
from gui.address_gui import AddressGui
from shipper.shipment import Shipment, parse_amherst_address_string


def address_from_direct_search(client: DespatchBaySDK, postcode: str, search_terms: Iterable) -> Address | None:
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



def get_explicit_match(shipment: Shipment, candidate_address:Address) -> Address | None:
    """ compares various shipment details to address, return address is matched else None"""
    if candidate_address.company_name:
        if shipment.customer in candidate_address.company_name \
                or candidate_address.company_name in shipment.customer \
                or shipment.delivery_name in candidate_address.company_name \
                or candidate_address.company_name in shipment.delivery_name:
            return candidate_address

    if shipment.str_to_match == candidate_address.street:
        return candidate_address

    else:
        return None


def check_address_company(address: Address, shipment: Shipment) -> Address | None:
    """compares address.company_name to shipment [customer, address_as_str, delivery_name]"""

    if not address.company_name:
        logger.info(f'No company name at address - passing check')
        return address

    if address.company_name == shipment.customer \
            or address.company_name in shipment._address_as_str \
            or address.company_name in shipment.delivery_name:
        logger.info(f'Address company name matches customer')
        return address

    else:
        pop_msg = f'Company name @Found Address and Shipment Customer Name do not exactly match' \
                  f'\n\nDatabase Details:' \
                  f'\nCustomer = {shipment.customer}' \
                  f'\nDelivery Name= {shipment.delivery_name}' \
                  f'\nString Address from database=' \
                  f'\n{shipment._address_as_str}' \
                  f'\n\nFound Address Details:'\
                  f'\nAddress Company Name= {address.company_name}' \
                  f'\nStreet addres= {address.street}' \
                  f'\n\n[Yes] to accept matched address or [No] to edit / replace'

        answer = sg.popup_yes_no(pop_msg, line_width=100)
        return address if answer == 'Yes' else None


def get_candidate_keys(client: DespatchBaySDK, postcode) -> dict:
    """takes a client and postcode, returns a dict with keys= dbay addresses as strings and values =  dbay address keys"""
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

def fuzzy_address(client, shipment) -> Address | BestMatch:
    """ takes a client, shipment and candidate_keys dict, returns a fuzzy matched address"""
    candidate_keys = get_candidate_keys(client=client, postcode=shipment.postcode)
    fuzzyscores = []
    for address_str, key in candidate_keys.items():
        # use backoff in case of postcodes with 70+ addresses. yes they exist - ask me how I know
        candidate_address = retry_with_backoff(client.get_address_by_key, retries=5, backoff_in_seconds=60, key=key)
        logger.info(f"{candidate_address=}")
        address = get_explicit_match(shipment=shipment, candidate_address=candidate_address)
        if isinstance(address, Address):
            return address
        else:
            fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
    else:
        logger.info(f'No exact match found, trying fuzzy match')
        bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
        logger.info(f'Bestmatch Address: {bestmatch.address}')
        return bestmatch

    ################

    # try:
    #     shipment.bestmatch = get_bestmatch(client=client, shipment=shipment)  # candidate key x api call
    #     log_str = "\n".join(f"{key} : {value}" for key, value in candidate_keys.items())
    #     logger.info(f"CANDIDATE KEYS :\n{log_str}")
    #     logger.info(f"BESTMATCH : {shipment.bestmatch}")
    # except RateLimitException:
    #     logger.info("API CALLS EXCEEDED ABANDONING SEARCH")
    #     return None
    # return shipment.bestmatch.address


def address_from_gui(client, sandbox: bool, outbound: bool, shipment, starter_address:Address) -> Address:
    address_gui = AddressGui(outbound=outbound, sandbox=sandbox, client=client, shipment=shipment,
                             address=starter_address,
                             contact=shipment.remote_contact)
    address_gui.get_address()
    address = address_gui.address
    logger.info(f'ADDRESS FROM GUI - {shipment.shipment_name_printable} - {address=}')
    return address


""" GET CONTACT?"""

def sender_from_address_id(client: DespatchBaySDK, address_id:str) -> Sender:
    """ return a dbay sender object representing home address defined in toml / Shipper.config"""
    return client.sender(address_id=address_id)


def get_home_recipient(client: DespatchBaySDK, config: Config) -> Recipient:
    """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
    address = client.get_address_by_key(config.home_address.dbay_key)
    return client.recipient(
        recipient_address=address, **config.home_contact.__dict__)


def recip_from_contact_and_key(client: DespatchBaySDK, dbay_key:str, contact:Contact) -> Recipient:
    """ return a dbay recipient object"""
    return client.recipient(recipient_address=client.get_address_by_key(dbay_key), **contact.__dict__)


def sender_from_contact_address(client: DespatchBaySDK, contact: Contact,
                                remote_address: Address) -> Sender:
    sender = client.sender(
        sender_address=remote_address, **contact.__dict__)
    return sender


def get_remote_recipient(contact: Contact, client: DespatchBaySDK, remote_address: Address) -> Sender:
    recip = client.recipient(
        # recipient_address=remote_address, **contact._asdict())
        recipient_address=remote_address, **contact.__dict__)
    # logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {recip}')
    return recip


def recip_from_contact_address( client: DespatchBaySDK, contact: Contact, address: Address) -> Sender:
    recip = client.recipient(
        # recipient_address=remote_address, **contact._asdict())
        recipient_address=address, **contact.__dict__)
    # logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {recip}')
    return recip


# depric

# def get_candidate_keys_dict(shipment: Shipment, client: DespatchBaySDK, postcode=None) -> dict:
#     """ return a dict of dbay addresses and keys, from postcode or shipment.postcode,
#         popup if postcode no good """
#     postcode = postcode or shipment.postcode
#     candidate_keys_dict = None
#     while not candidate_keys_dict:
#         try:
#             candidate_keys_dict = {candidate.address: candidate.key for candidate in
#                                    client.get_address_keys_by_postcode(postcode)}
#         except ApiException as e:
#             postcode = sg.popup_get_text(f'Bad postcode for {shipment.customer} - Please Enter')
#             if postcode is None:
#                 break
#             continue
#         else:
#             return candidate_keys_dict

#
# def get_bestmatch(client: DespatchBaySDK, shipment: Shipment, candidate_keys, ) -> BestMatch:
#     fuzzyscores = []
#     for address_str, key in candidate_keys.items():
#         candidate_address = client.get_address_by_key(key)
#         if explicit_match := get_explicit_bestmatch(candidate_address=candidate_address, shipment=shipment):
#             return explicit_match
#         else:
#             fuzzyscores.append(get_fuzzy_scores(candidate_address=candidate_address, shipment=shipment))
#     else:
#         # finished loop, no explicitmatch from candidates so get a bestmatch from fuzzyscores
#         bestmatch = bestmatch_from_fuzzyscores(fuzzyscores=fuzzyscores)
#         return bestmatch
#
#
# def get_explicit_bestmatch(shipment: Shipment, candidate_address) -> BestMatch | None:
#     """ compares shipment details to address, return a bestmatch if an explicit match is found  else None"""
#
#     if shipment.customer == candidate_address.company_name \
#             or shipment.str_to_match == candidate_address.street \
#             or shipment.delivery_name == candidate_address.company_name:
#         return BestMatch(address=candidate_address, category='explicit', score=100,
#                          str_matched=shipment.str_to_match)
#     else:
#         return None



# depric or notes or something?


# def get_remote_sender_recip(client, outbound:bool, remote_address:Address, remote_contact:Contact):
#     if outbound:
#         return get_remote_recipient(client=client, remote_address=remote_address, contact=remote_contact)
#     else:
#         return get_remote_sender(client=client, remote_address=remote_address, contact=remote_contact)


# def get_remote_sender_recip(client1, config1, shipment: Shipment, home_sender_recip: Sender | Recipient):
#     client = client1
#     config = config1
#     remote_address = None
#     while not remote_address:
#         remote_address = get_remote_address(config1, shipment=shipment, client=client)
#
#     if config.outbound:
#         shipment.sender = home_sender_recip
#         shipment.recipient = get_remote_recipient(client=client, remote_address=remote_address,
#                                                   contact=shipment.remote_contact)
#     else:
#         shipment.sender = get_remote_sender(client=client, remote_address=remote_address,
#                                             contact=shipment.remote_contact)
#         shipment.recipient = home_sender_recip


#
#
# def address_from_logic(client: DespatchBaySDK, shipment: Shipment, sandbox: bool) -> Address | None:
#     # if address := address_from_search(client=client, shipment=shipment):
#     terms = {shipment.customer, shipment.delivery_name,
#              parse_amherst_address_string(str_address=shipment._address_as_str)}
#
#     if address := address_from_searchterms(client=client, postcode=shipment.postcode, search_terms=terms):
#         if sandbox:
#             # then nothing will match so give up now
#             return address
#         if checked_address := check_address_company(address=address, shipment=shipment):
#             logger.info(f"Address Passed Company Name Check")
#             return checked_address
#     return None
#
