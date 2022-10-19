# # fires "HelloWorld" to commence agent triggers
# import win32com.client  # requires pywin32 package
#
# cmc = win32com.client.Dispatch("Commence.DB")  # talk to Commence
# conv = cmc.GetConversation("Commence", "GetData")  # fire up 'DDE'
# # first create an Commence Agent triggering on receive DDE string HelloWorld
# # that (for instance) displays a MessageBox
# dde = "[FireTrigger(HelloWorld)]"  # see help files for much more useful stuff
# conv.Execute(dde)  # execute DDE command, hopefully Commence listens


""" fires "HelloWorld" too commence agent triggers
import win32com.client  # requires pywin32 package

cmc = win32com.client.Dispatch("Commence.DB")  # talk to Commence
conv = cmc.GetConversation("Commence", "GetData")  # fire up 'DDE'
# first create an Commence Agent triggering on receive DDE string HelloWorld
# that (for instance) displays a MessageBox
dde = "[FireTrigger(HelloWorld)]"  # see help files for much more useful stuff
conv.Execute(dde)  # execute DDE command, hopefully Commence listens
"""

import os

os.startfile(r"C:\AmDesp\data\Parcelforce Labels\CALM All Porsche Trophy-2022-10-21.pdf", "print")

# import subprocess
#
# doc_ref = r'file:///C:/Users/giles/Downloads/Order-2292544-Docs-021021.pdf'
#
# command = (r'C:\AmDesp\PDFtoPrinter.exe', doc_ref)
# subprocess.call(command, shell=True)

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
