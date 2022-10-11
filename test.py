import subprocess

doc_ref = r'C:\AmDesp\data\Parcelforce Labels\Rakesh Chandraker-2022-10-11.pdf'


def command_print(pdf_to_print: str, doc_ref: str, event=None) -> None:
    command = "{} {}".format(pdf_to_print, doc_ref)
    subprocess.call(command, shell=True)


# command_print(r'C:\AmDesp\bin\PDFtoPrinter.exe', doc_ref)


command = (r'C:\AmDesp\PDFtoPrinter.exe', doc_ref)
subprocess.call(command, shell=True)

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
