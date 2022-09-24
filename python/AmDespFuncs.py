import json
import xml.etree.ElementTree as ET
from datetime import datetime

from python.utils_pss.utils_pss import *
from .AmDespClasses import Hire


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
            shipment.update({'Customer': shipment['To Customer']})
            shipment.update({'hireName': shipment['Name']})
            shipment.update({'deliveryAddress': shipment['Delivery Address']})
            shipment = cleanDictShip(shipment)
            manifest.append(shipment)
    print("Manifest imported with ", len(manifest), "shipments\n")
    return manifest


def clean_hire_dict(dict):  # if list takes first item!
    newdict = {}
    for k, v in dict.items():
        k = unsanitise(k)
        if v: v = unsanitise(v)
        k = toCamel(k)
        if isinstance(v, list):
            v = v[0]
        v = v.replace(",", "")
        if v.isnumeric():
            v = int(v)
            if v == 0:
                v = None
        elif v.isalnum():
            v = v.title()
        if 'Price' in k:
            v=float(v)
            ...
        if k == "sendOutDate":
            v = datetime.strptime(v, '%d/%m/%Y').date()
        newdict.update({k: v})
    newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
    # newdict = {k: v for k, v in newdict.items() if k in HIREFIELDS}
    # newdict = {k: v for k, v in newdict.items() if k not in expungedFields}
    return (newdict)


def cleanDictShip(dict):  # if list takes first item!
    # print("Cleaning your shipdict\n")
    newdict = {}
    for k, v in dict.items():
        k = unsanitise(k)
        if v: v = unsanitise(v)
        if k in com_fields: k = com_fields[k]
        k = toCamel(k)
        if isinstance(v, list):
            v = v[0]
        if v.replace(",", "").isnumeric():
            v = v.replace(",", "")
        if v.isnumeric():
            v = int(v)
            if v == 0:
                v = None
        elif v.isalnum():
            v = v.title()
        if k == "SendOutDate":
            v = datetime.strptime(v, '%d/%m/%Y').date()

        newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        newdict = withoutKeys(newdict, expungedFields)  # in confiig
        newdict.update({k: v})
        # if v: print("UPDATED:",k," - ", v)
    return (newdict)


def hire_from_xml(xml):  # currently hardcoded xml link.... breaks otherwise... how to passfile refs/paths?
    # TODO handle xmls with multiple shipments
    hire_dict = {}
    newxml = "C:\AmDesp\data\AmShip.xml"
    newxml= f"{xml}"
    tree = ET.parse(xml)
    root = tree.getroot()
    fields = root[0][2]
    customer = root[0][3].text  # debug
    for field in fields:
        k = field[0].text
        v = field[1].text
        if v:
            hire_dict.update({k: v})
    hire_dict.update({'customer': customer})
    hire_dict = clean_hire_dict(hire_dict)
    print("Xml hire with", len(hire_dict), "fields imported")
    return hire_dict


def ship_hire(hiredict): # Runs class methods to ship a hire object
    oHire = Hire(hiredict)
    oShip = oHire.make_shipment()
    oShip.val_boxes()
    oShip.val_dates()
    oShip.val_address()
    oShip.change_add()
    oShip.make_request()
    oShip.queue()

