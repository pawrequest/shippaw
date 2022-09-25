import json

from config import *

with open(DIR_DATA / 'AmShip.json') as x:
    print(type(x))
    obj = json.load(x)
    ship_list = []
    ship_list.append(obj)

    print(ship_list)

# python object to be appended

# parsing JSON string:

# appending the shipmentJson
# z.update(y)
#
# # the result is a JSON string:
# print(json.dumps(z))





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


# def shipmentFromXml(xml):
#     shipment = {}
#     tree = ET.parse(xml)
#     root = tree.getroot()
#     fields = root[0][2]
#     connections = root[0][3]
#     for connection in connections.iter():
#         print (connection.text)
#     eltags = [elem.tag for elem in connections.iter()]  # quick look
#     # print(eltags[2])
#
#     cat = root[0][0].text
#     for field in fields:
#         fieldname = field[0].text
#         fieldvalue = field[1].text
#         shipment[fieldname] = fieldvalue
#         shipment[category] = cat
#     return shipment
# shipmentFromXml(xmlfile)
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
