from pathlib import Path

from amdesp.despatchbay.despatchbay_entities import Service, Sender, Recipient, Parcel


import datetime
import pathlib

from amdesp.despatchbay.despatchbay_entities import Service, Sender, Recipient, Parcel


class Shipment:
    def __init__(self, ship_dict: dict, is_return: bool = False):
        """
        :param ship_dict: a dictionary of shipment details
        :param is_return: recipient is user's own sender_address[0]
        """
        self.label_location: pathlib.Path = pathlib.Path()
        self.company_name:str = ''
        self.service:Service | None = None
        self.sender:Sender|None = None
        self.recipient:Recipient|None = None
        self.parcels:[Parcel] = []
        self.collection_booked:bool = False
        self.printed:bool = False
        self.service_menu_map:dict = dict()
        self.date_menu_map:dict = dict()
        self.category:str = ship_dict['category']
        self.shipment_name:str = ship_dict['shipment_name']
        self.date:datetime.date = ship_dict['date']
        self.address_as_str:str = ship_dict['address_as_str']
        # self.contact:str = ship_dict.get('contact', None)
        # if self.contact is None:
        #     self.contact = ship_dict.get('contact_name', None)
        self.contact = next((ship_dict.get(key) for key in ['contact', 'contact_name'] if key in ship_dict), None)
        self.postcode:str = ship_dict['postcode']
        self.boxes:int = ship_dict['boxes']
        self.status:str = ship_dict['status']
        self.email:str = ship_dict['email']
        self.telephone:str = ship_dict['telephone']
        self.customer:str = ship_dict['customer']
        self.is_return:bool = is_return
        self.inbound_id:str|None = ship_dict.get('inbound_id', None)
        self.outbound_id:str|None = ship_dict.get('outbound_id', None)
        self.search_term:str = parse_amherst_address_string(self.address_as_str)


def parse_amherst_address_string(str_address: str):
    firstline = str_address.strip().split("\n")[0]
    first_block = (str_address.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    for char in firstline:
        if not char.isalnum() and char != " ":
            firstline = firstline.replace(char, "")

    if first_char.isnumeric():
        return first_block
    else:
        return firstline
