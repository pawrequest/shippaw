import xml.etree.ElementTree as ET
from datetime import datetime

from config_f import *
from shipment_class_f import *


def unsanitise(string):
    string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
                                                                                                            chr(60)).replace(
        "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    return string

def shipment_from_xml(xml):
    shipment = Shipment()
    tree = ET.parse(xml)
    root = tree.getroot()
    fields = root[0][2]
    connected_customer = root[0][3][1][0][0].text
    cat = root[0][0].text.lower()
    for field in fields:
        if field[0].text:
            fieldname = field[0].text.lower()
            fieldname = unsanitise(fieldname)
            if " " in fieldname:
                fieldname = fieldname.replace(" ", "_")
            if fieldname in com_fields.keys():  # debug
                fieldname = com_fields[fieldname]
            if field[1].text:
                fieldvalue = field[1].text
                fieldvalue = unsanitise(fieldvalue)
                if fieldvalue.isnumeric():
                    fieldvalue = int(fieldvalue)
                    if fieldvalue == 0:
                        fieldvalue = None
                setattr(shipment, fieldname, fieldvalue)
    setattr(shipment, category, cat)
    print(shipment.send_date)
    if cat.lower() == "deliveryCustomer":
        print("IS A CUSTOMER")
        shipment.send_date = datetime.today().date()
    elif cat.lower() == "hire":
        print("IS A HIRE")
        setattr(shipment, customer, connected_customer)
        shipment.send_date = datetime.strptime(shipment.send_date, '%d/%m/%Y').date()
    return shipment