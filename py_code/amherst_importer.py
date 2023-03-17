import xml.etree.ElementTree as ET
import re
from datetime import datetime
DT_DISPLAY = '%A - %B %#d'
DT_HIRE = '%d/%m/%Y'
DT_DB = '%Y-%m-%d'
DT_EXPORT = '%d-%m-%Y'
class AmherstImport:
    def __init__(self, xml_file, CNFG):
        pattern = re.compile(r"\bdeliv\b")

        self.shipment_name = None
        self.send_out_date = None
        self.delivery_email = None
        self.delivery_tel = None
        self.delivery_contact = None
        self.delivery_address = None
        self.delivery_postcode = None
        self.shipment_id_inbound = None
        self.shipment_id_outbound = None
        self.boxes = 0

        # inspect xml
        tree = ET.parse(xml_file)
        root = tree.getroot()
        fields = root[0][2]
        category = root[0][0].text

        shipment_fields = CNFG.shipment_fields
        ship_dict = dict()
        for field in fields:
            k = field[0].text
            k = to_snake_case(k)
            v = field[1].text
            if v:
                k = self.unsanitise(k)
                v = self.unsanitise(v)

                if "Number" in k:
                    v = v.replace(',', '')
                if k == 'name':
                    k = 'shipment_name'
                # if pattern.search(k):
                if k[:6] == "deliv ":
                    k = k.replace('deliv', 'delivery')
                if k == 'delivery_telephone':
                    k = 'delivery_tel'
                ship_dict.update({k: v})
                if k in CNFG.shipment_fields:
                    setattr(self, k, v)

        if category == "Hire":
            self.customer = root[0][3].text

        elif category == "Customer":
            self.customer = fields[0][1].text
            self.shipment_name = f'{self.shipment_name} - {datetime.now():{DT_EXPORT}}'

        elif category == "Sale":
            self.customer = root[0][3].text

        if self.send_out_date is None:
            self.send_out_date = datetime.today().strftime(DT_HIRE)

        self.category = category
        self.ship_dict = ship_dict
        # noinspection PyTypeChecker
        self.search_term = self.parse_amherst_address_string(self.delivery_address)

        for attr_name in shipment_fields:
            if attr_name not in vars(self):
                if attr_name not in ['delivery_cost', 'delivery_telephone']:
                    print(f"*** Warning - {attr_name} not found in ship_dict - Warning ***")

    def parse_amherst_address_string(self, str_address):
        # crapstring = self.deliveryAddress
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

    def unsanitise(self, input_string):
        """ deals with special and escape chars"""
        input_string = input_string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;",
                                                                                                 chr(39)).replace(
            "&lt;",
            chr(60)).replace(
            "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
        return input_string

    def clean_ship_dict(self, dict) -> dict:
        """
        cleans your dict

        :param dict:
        :return:
        """
        pattern = re.compile(r"\bdeliv\b")


        newdict = {}
        for k, v in dict.items():
            if "deliv" in k:
                if "delivery" not in k:
                    k = k.replace('deliv', 'delivery')

            if v:
                v = self.unsanitise(v)
                if isinstance(v, list):
                    v = v[0]
                if v.isnumeric():
                    v = int(v)
                    if v == 0:
                        v = None
                elif v.isalnum():
                    v = v.title()
                if 'Price' in k:
                    v = float(v)

            newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        return newdict


def to_snake_case(input_string):
    """Convert a string to lowercase snake case."""
    # Replace spaces with underscores
    input_string = input_string.replace(" ", "_")
    # Replace any non-alphanumeric characters with underscores
    input_string = ''.join(c if c.isalnum() else '_' for c in input_string)
    # Convert to lowercase
    input_string = input_string.lower()
    return input_string
