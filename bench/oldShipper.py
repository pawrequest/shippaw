from pprint import pprint

from py_code.one_dbase import Amherst_one_dbase


class Shipment(Amherst_one_dbase):
    def __init__(self, app, single_dbase, is_return=False):
        """
        :param ship_dict: a dictionary of shipment details
        :param config: a config() object
        :param reference:
        :param label_text:
        """
        super().__init__(single_dbase)
        # xml_file = app.xml
        # attrs from importer class
        # super().__init__(xml_file, config)

        config = app.config
        client = app.client

        self.home_sender = client.sender(
            address_id=config.home_sender_id,
            name=config.home_address['contact'],
            email=config.home_address['email'],
            telephone=config.home_address['telephone'],
            sender_address=client.get_sender_addresses()[0]
        )
        self.home_recipient = client.recipient(
            name=config.home_address['contact'],
            email=config.home_address['email'],
            telephone=config.home_address['telephone'],
            recipient_address=client.find_address(config.home_address['postal_code'],
                                                  config.home_address['search_term'])

        )

        if DEBUG:
            pprint(f"\n{self=}\n")
