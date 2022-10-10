# import json
# import xml.etree.ElementTree as ET
# from datetime import datetime
#
# from python.utils_pss.utils_pss import *
# from .AmDespApp import Hire
#
#
# def manifestFromJson(manifest_list_dict) -> list:
#     # TODO: does this still work?
#     print("Parsing Json\n")
#     manifest = []
#     with open(manifest_list_dict) as f:
#         json_data = json.load(f)
#         cat = json_data['CommenceCategory']
#         manifest_data = json_data['Items']
#         for shipment in manifest_data:
#             # newship = {}
#             shipment.update({'category': cat})
#             shipment.update({'customer': shipment['To Customer']})
#             shipment.update({'hireName': shipment['Name']})
#             shipment.update({'deliveryAddress': shipment['Delivery Address']})
#             shipment = cleanDictShip(shipment)
#             manifest.append(shipment)
#     print("Manifest imported with ", len(manifest), "shipments\n")
#     return manifest
#
#
# def clean_xml_hire(dict) -> dict:
#     newdict = {}
#     for k, v in dict.items():
#
#         k = unsanitise(k)
#         k = toCamel(k)
#
#         if v:
#             v = unsanitise(v)
#             if isinstance(v, list):
#                 v = v[0]
#             if v.isnumeric():
#                 v = int(v)
#                 if v == 0:
#                     v = None
#             elif v.isalnum():
#                 v = v.title()
#             if 'Price' in k:
#                 v=float(v)
#             if "Number" in k:
#                 v = v.replace(",", "")
#             if k == "sendOutDate":
#                 v = datetime.strptime(v, '%d/%m/%Y').date()
#
#         newdict.update({k: v})
#     newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
#     # newdict = {k: v for k, v in newdict.items() if k in HIREFIELDS}
#     # newdict = {k: v for k, v in newdict.items() if k not in expungedFields}
#     return (newdict)
#
# #
# # def cleanDictShip(dict):  # if list takes first item!
# #     # print("Cleaning your shipdict\n")
# #     newdict = {}
# #     for k, v in dict.items():
# #         k = unsanitise(k)
# #         if v: v = unsanitise(v)
# #         if k in com_fields: k = com_fields[k]
# #         k = toCamel(k)
# #         if isinstance(v, list):
# #             v = v[0]
# #         if v.replace(",", "").isnumeric():
# #             v = v.replace(",", "")
# #         if v.isnumeric():
# #             v = int(v)
# #             if v == 0:
# #                 v = None
# #         elif v.isalnum():
# #             v = v.title()
# #         if k == "SendOutDate":
# #             v = datetime.strptime(v, '%d/%m/%Y').date()
# #
# #         newdict.update({k: v})
# #         newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
# #         newdict = withoutKeys(newdict, expungedFields)  # in confiig
# #         newdict.update({k: v})
# #         # if v: print("UPDATED:",k," - ", v)
# #     return (newdict)
#
#
#
#
# def obj_from_xml(xml):
#
#     obj_dict = {}
#     tree = ET.parse(xml)
#     root = tree.getroot()
#     fields = root[0][2]
#     customer = root[0][3].text  # debug
#     for field in fields:
#         k = field[0].text
#         if "Number" in k:
#             v=v.replace(",","")
#         v = field[1].text
#         if v:
#             hire_dict.update({k: v})
#     hire_dict.update({'customer': customer})
#     hire_dict = clean_xml_hire(hire_dict)
#     print("Xml hire with", len(hire_dict), "fields imported")
#     return hire_dict
#
# def hire_from_xml(xml):
#     # TODO handle xmls with multiple shipments
#     hire_dict = {}
#     tree = ET.parse(xml)
#     root = tree.getroot()
#     fields = root[0][2]
#     customer = root[0][3].text  # debug
#     for field in fields:
#         k = field[0].text
#         if "Number" in k:
#             v=v.replace(",","")
#         v = field[1].text
#         if v:
#             hire_dict.update({k: v})
#     hire_dict.update({'customer': customer})
#     hire_dict = clean_xml_hire(hire_dict)
#     print("Xml hire with", len(hire_dict), "fields imported")
#     return hire_dict
#
#
# def ship_hire(hiredict): # Runs class methods to ship a hire object
#     oHire = Hire(hiredict)
#     oShip = oHire.make_shipment()
#     oShip.val_boxes()
#     oShip.val_dates()
#     oShip.val_address()
#     oShip.change_add()
#     oShip.make_request()
#     oShip.queue()

