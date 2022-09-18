# import inspect
# from pprint import pprint
#
# # local namespace
# print(inspect.currentframe().f_locals)
#
# # next outer frame object (this frame’s caller)
# print(inspect.currentframe().f_back)
#
# # sourcecode line
# pprint(inspect.currentframe().f_lineno)
#
#
# TM5*er1ng
### make shipment_dict from xml
import xml.etree.ElementTree as ET
from pprint import pprint

from config import *

xmlfile = "C:\AmDesp\item_export.xml"
def shipment_from_xml(xml):
    shipment = {}
    tree = ET.parse(xml)
    root = tree.getroot()
    # print(root.items())
    fields = root[0][2]
    cat = root[0][0].text

    for field in fields:
        fieldname = field[0].text
        fieldvalue = field[1].text
        shipment[fieldname] = fieldvalue
        shipment[category] = cat

    return shipment

pprint(shipment_from_xml(xmlfile))

# for fields in record:
#     print(fields.items())

#     for field in fields:
        # print(field.tag, field.text,"\n")
        # shipment[]

# eltags = [elem.tag for elem in root.iter()] # quick look


# for neighbor in root.iter():
#     print(neighbor.text)
# print("RECORD ITEMS",record.attrib)
# for field in record.iter('Field'):
#     print("field tag",field.tag," - ", field.text)

