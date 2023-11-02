import logging
import sys
from typing import Iterable

import PySimpleGUI as sg
from despatchbay.despatchbay_entities import Address, Recipient, Sender
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import ApiException

from ..core.entities import Contact, HomeAddress, AddressMatch
from ..gui.address_gui import address_from_gui
from .fuzzy import fuzzy_address_script

logger = logging.getLogger(__name__)


def remote_address_script(shipment: 'ShipmentInput', remote_contact: Contact, client: DespatchBaySDK) -> (Address | bool):
    """ Gets an Address object representing the remote location. tries direct search, then fuzzy search, then gui entry."""
    terms = {shipment.customer, shipment.delivery_name, shipment.str_to_match}

    if address := address_from_direct_search(postcode=shipment.postcode, search_terms=terms, client=client):
        shipment.remote_address_matched = AddressMatch.DIRECT
        return address

    fuzzy = fuzzy_address_script(shipment=shipment, client=client)
    while True:
        address = address_from_gui(shipment=shipment, address=fuzzy, contact=remote_contact, client=client)
        if address is None:
            if sg.popup_yes_no(f"If you don't enter an address the shipment for {shipment.customer_printable} "
                               f"will be skipped. \n'Yes' to skip, 'No' to try again") == 'Yes':
                sg.popup_ok("it would crash now and i'm nt fixing it, so exit goodbye")
                sys.exit(666)
            continue
        else:
            shipment.remote_address_matched = AddressMatch.GUI
            return address


def address_from_direct_search(postcode: str, search_terms: Iterable, client: DespatchBaySDK) -> Address | None:
    """ return address from postcode and search terms, or None if no address found."""
    check_set = set(search_terms)
    for term in check_set:
        try:
            address = client.find_address(postcode, term)
            logger.info(
                f"Address Match Success : {f'{postcode=} | address={address.company_name} - ' if address.company_name else ''}{address.street}")
            return address
        except ApiException as e1:
            if 'No Addresses Found At Postcode' in str(e1):
                logger.info(f"Address Match Fail : {postcode=} | {term=}")
            continue
        except Exception as e2:
            logger.exception(f"Unknown exception in address_from_direct_search {str(e2)}")
            continue
    else:
        logger.info(f"ALL ADDRESS SEARCHES FAIL - {postcode=} | {check_set=}")
        sg.popup_ok("Address Not Matched - please check it and consider updating Commence")
        return None


def sender_or_recipient_from_home_address(home_contact: Contact, home_address: HomeAddress, outbound: bool,
                                          client: DespatchBaySDK) -> Sender | Recipient:
    """returns a sender object from home_address_id or recipient from home_address.dbay_key representing home address"""
    if outbound:
        return client.sender(address_id=home_address.address_id)
    else:
        address = client.get_address_by_key(home_address.dbay_key)
        return client.recipient(recipient_address=address, **home_contact.__dict__)

