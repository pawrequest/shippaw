from despatchbay.despatchbay_entities import Sender, Recipient, Address
from despatchbay.despatchbay_sdk import DespatchBaySDK

from shipper.addresser import get_remote_address
from core.config import Config, get_amdesp_logger
from core.enums import Contact
from shipper.shipment import Shipment

logger = get_amdesp_logger()
def get_remote_sender_recip(client1, config1, shipment: Shipment, home_sender_recip: Sender | Recipient):
    client = client1
    config = config1
    remote_address = None
    while not remote_address:
        remote_address = get_remote_address(config1, shipment=shipment, client=client)

    if config.outbound:
        shipment.sender = home_sender_recip
        shipment.recipient = get_remote_recipient(client=client, remote_address=remote_address,
                                                  contact=shipment.remote_contact)
    else:
        shipment.sender = get_remote_sender(client=client, remote_address=remote_address,
                                            contact=shipment.remote_contact)
        shipment.recipient = home_sender_recip


def get_home_sender(client: DespatchBaySDK, config: Config) -> Sender:
    """ return a dbay sender object representing home address defined in toml / Shipper.config"""
    return client.sender(address_id=config.home_address.address_id)


def get_home_recipient(client: DespatchBaySDK, config: Config) -> Recipient:
    """ return a dbay recipient object representing home address defined in toml / Shipper.config"""
    address = client.get_address_by_key(config.home_address.dbay_key)
    return client.recipient(
        recipient_address=address, **config.home_contact.__dict__)


def get_remote_sender(client: DespatchBaySDK, contact: Contact,
                      remote_address: Address) -> Sender:
    sender = client.sender(
        sender_address=remote_address, **contact.__dict__)
    return sender


def get_remote_recipient(contact: Contact, client: DespatchBaySDK, remote_address: Address) -> Sender:
    recip = client.recipient(
        # recipient_address=remote_address, **contact._asdict())
        recipient_address=remote_address, **contact.__dict__)
    logger.info(f'PREP SHIPMENT - REMOTE RECIPIENT {recip}')
    return recip
