class Shipment:
    def __init__(self, ship_dict: dict, is_return: bool = False):
        """
        :param ship_dict: a dictionary of shipment details
        :param is_return: recipient is user's own sender_address[0]
        """
        self.label_location = None
        self.company_name = None
        self.service = None
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = None
        self.printed = None
        self.service_menu_map = dict()
        self.date_menu_map = dict()
        self.category = ship_dict['category']
        self.shipment_name = ship_dict['shipment_name']
        self.date = ship_dict['send_out_date']
        self.address_as_str = ship_dict['address_as_str']
        self.contact = ship_dict['contact']
        self.postcode = ship_dict['postcode']
        self.boxes = ship_dict['boxes']
        self.status = ship_dict['status']
        self.email = ship_dict['email']
        self.telephone = ship_dict['telephone']
        self.customer = ship_dict['customer']
        self.is_return = is_return
        self.inbound_id = ship_dict.get('inbound_id', None)
        self.outbound_id = ship_dict.get('outbound_id', None)
        self.search_term = parse_amherst_address_string(self.address_as_str)


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
