from pprint import pprint

import PySimpleGUI as sg

class Shipment():
    def __init__(self, app, ship_dict, is_return=False):
        """
        :param ship_dict: a dictionary of shipment details
        :param config: a config() object
        :param reference:
        :param label_text:
        """

        self.shipment_name = ship_dict['shipment_name']
        self.date = ship_dict['send_out_date']
        self.address_as_str = ship_dict['address_as_str']
        self.contact = ship_dict['contact']
        self.company_name = None
        self.postcode = ship_dict['postcode']
        self.boxes = ship_dict['boxes']
        self.status = ship_dict['status']
        self.email = ship_dict['email']
        self.telephone = ship_dict['telephone']
        self.customer = ship_dict['customer']
        self.is_return = is_return
        self.id_inbound = ship_dict.get('inbound_id', None)
        self.id_outbound = ship_dict.get('outbound_id', None)
        self.service = None
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = False


        config = app.config
        client = app.client
        while True:
            try:
                if self.is_return:
                    self.recipient = client.recipient(
                        name=config.home_address['contact'],
                        email=config.home_address['email'],
                        telephone=config.home_address['telephone'],
                        recipient_address=client.get_sender_addresses()[0]
                    )
                else:
                    self.sender = client.sender(
                        address_id=config.home_sender_id,
                        name=config.home_address['contact'],
                        email=config.home_address['email'],
                        telephone=config.home_address['telephone'],
                        sender_address=client.get_sender_addresses()[0]
                    )

            except Exception as e:
                response = sg.popup_get_text("Problem with configured home address, enter postcode then searchterm (; separated")
                postcode = response.split(';')[0]
                search = response.split(';')[1]
                continue
            else:
                break
        # self.available_dates = client.get_available_collection_dates(self.sender, config.courier_id)  # get dates


    def get_sender_recip(self, app):
        client = app.client

        # shipment is a return so recipient is homebase
        if self.is_return:
            try:
                sender_address = client.find_address(self.postcode, self.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                sender_address = self.gui.address_chooser(candidates)
            sender = client.sender(name=self.name, email=self.email,
                                   telephone=self.telephone, sender_address=sender_address)

        # not a return so we are sender
        if not self.is_return:
            sender = self.home_sender
            try:
                recipient_address = client.find_address(self.postcode, self.search_term)
            except:
                candidates = self.gui.get_address_candidates()
                recipient_address = self.gui.address_chooser(candidates)
            recipient = client.recipient(name=self.name, email=self.email,
                                         telephone=self.telephone, recipient_address=recipient_address)

            self.sender, self.recipient = sender, recipient

        return sender, recipient
