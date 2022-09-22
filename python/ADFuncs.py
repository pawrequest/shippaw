import json
import xml.etree.ElementTree as ET

from config import *
from python.utils_pss.utils_pss import *


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
    # newxml = "C:\AmDesp\shipmentJson\AmShip.xml"
    tree = ET.parse(xml)
    root = tree.getroot()
    fields = root[0][2]
    # add shipment-wide
    customer = root[0][3][1][0][0].text
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


def manifestFromJson(manifest_list_dict):
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
    # print("Cleaning your shipDict\n")
    newdict = {}
    for k, v in dict.items():
        if k in com_fields: k = com_fields[k]
        k = toCamel(k)
        # k = inflection.camelize(k, False).replace(" ","")
        if isinstance(v, list):
            v = v[0]
        if v.replace(",", "").isnumeric() and int(v.replace(',', '')) == 0:
            v = None
        elif v.isalnum():
            v = v.title()

        if k == "hireRef":
            v = v.replace(",", "")
            if v.isnumeric():
                v = int(v)
            newdict.update({"id": int(v)})

        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        newdict = withoutKeys(newdict, expungedFields)  # in confiig
        newdict.update({k: v})
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
