import json
import xml.etree.ElementTree as ET

from config import *
from .AmDespClasses import Shipment


# from python.utils_pss.utils_pss import *


def JsonToShippies(jsondata):
    shippies = []
    manifest = manifestFromJson(jsondata)
    for shipment in manifest:
        shippies.append(Shipment(shipment, shipment['id']))
    print("SHIPPIES:", shippies)
    return shippies


def XmlToShippy(xmlda):  # xmldata name being used?
    shipment = shipmentFromXml(xmlda)
    shippy = Shipment(shipment, shipment['customer'])
    print("Shippy:", shippy)
    return shippy


#


# def unsanitise(string):
#     # string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
#     #                                                                                                         chr(60)).replace(
#     #     "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
#     # return string
#     string = string.replace("&amp;", chr(38))
#     string = string.replace("&quot;", chr(34))
#     string = string.replace("&apos;", chr(39))
#     string = string.replace("&lt;", chr(60))
#     string = string.replace("&gt;", chr(62))
#     string = string.replace("&gt;", chr(32))
#     string = string.replace("&#", "")
#     string = string.replace(";", "")
#     return string


def shipmentFromXml(xml):
    # TODO handle xmls with multiple shipments
    shipment = {}
    newxml = "C:\AmDesp\data\AmShip.xml"
    tree = ET.parse(XMLFILE)
    root = tree.getroot()
    fields = root[0][2]
    # add shipment-wide

    customer = root[0][3].text  # debug

    print(customer)
    cat = root[0][0].text
    shipment['category'] = cat
    shipment['customer'] = customer
    for field in fields:
        k = field[0].text
        v = field[1].text
        if v:
            shipment.update({k: v})
    shipment = cleanDict(shipment)
    print("Xml shipment with", len(shipment), "fields imported\n")
    return shipment


def manifestFromJson(manifest_list_dict) -> list:
    print("Parsing Json\n")
    manifest = []
    with open(manifest_list_dict) as f:
        json_data = json.load(f)
        cat = json_data['CommenceCategory']
        manifest_data = json_data['Items']
        for shipment in manifest_data:
            # newship = {}
            shipment.update({'category': cat})
            shipment.update({'customer': shipment['To Customer']})
            shipment.update({'hireName': shipment['Name']})
            shipment.update({'dAddress': shipment['Delivery Address']})
            shipment = cleanDict(shipment)
            manifest.append(shipment)
    print("Manifest imported with ", len(manifest), "shipments\n")
    return manifest


def cleanDict(dict):  # if list takes first item!
    # print("Cleaning your shipdict\n")
    newdict = {}
    for k, v in dict.items():
        k=unsanitise(k)
        if v: v=unsanitise(v)
        if k in com_fields: k = com_fields[k]
        k = toCamel(k)
        if isinstance(v, list):
            v = v[0]
        if v.replace(",", "").isnumeric():
            v=v.replace(",", "")
        if v.isnumeric():
            v=int(v)
            if v == 0:
                v = None
        elif v.isalnum():
            v = v.title()

        newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        newdict = withoutKeys(newdict, expungedFields)  # in confiig
        newdict.update({k: v})
        # if v: print("UPDATED:",k," - ", v)
    return (newdict)



def parse_shipment_address(shipment):
    print("\n--- Parsing Address...\n")
    crapstring = shipment.d_address
    firstline = crapstring.split("\n")[0]
    first_block = (crapstring.split(" ")[0]).split(",")[0]
    first_char = first_block[0]
    shipment.firstline = firstline
    for char in firstline:
        if not char.isalpha():
            if not char.isnumeric():
                if not char == " ":
                    firstline = firstline.replace(char, "")
    if first_char.isnumeric():
        shipment.building_num = first_block
    else:
        print("- No building number, using firstline:", shipment.firstline, '\n')

    return shipment


def check_boxes(shipment):  # sent to class
    ui = ""
    while True:
        if shipment.boxes:
            print(line, "\n\t\t", shipment.customer, "|", shipment.firstline, "|", shipment.send_date)
            ui = input("[C]onfirm or Enter a number of boxes\n")
            if ui.isnumeric():
                shipment.boxes = int(ui)
                print("Shipment updated  |  ", shipment.boxes, "  boxes\n")
            if ui == 'c':
                return shipment
            continue
        else:
            print("\n\t\t*** ERROR: No boxes added ***\n")
            ui = input("- How many boxes?\n")
            if not ui.isnumeric():
                print("- Enter a number")
                continue
            shipment.boxes = int(ui)
            print("Shipment updated  |  ", shipment.boxes, "  boxes\n")
            return shipment
