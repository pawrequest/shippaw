import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pprint import pprint

from config import *
from python.utils_pss.utils_pss import *
from .AmDespClasses import Shipment


def JsonToShippies(jsondata):
    shippies = []
    manifest = manifestFromJson(jsondata)
    for shipment in manifest:
        shippies.append(Shipment(shipment, shipment['id']))
    print("SHIPPIES:", shippies)
    return shippies


def XmlToShippy(xmlda):  # xmldata name being used?
    shipment = shipmentFromXml(xmlda)
    shippy = Shipment(shipment, shipment['deliveryCustomer'])
    print("Shippy:", shippy)
    return shippy


def shipmentFromXml(xml):  # currently hardcoded xml link.... breaks otherwise... how to passfile refs/paths?
    # TODO handle xmls with multiple shipments
    shipment = {}
    newxml = "C:\AmDesp\data\AmShip.xml"
    tree = ET.parse(XMLFILE)
    root = tree.getroot()
    fields = root[0][2]
    # add shipment-wide

    customer = root[0][3].text  # debug

    cat = root[0][0].text
    shipment['category'] = cat
    shipment['deliveryCustomer'] = customer
    for field in fields:
        k = field[0].text
        v = field[1].text
        if v:
            shipment.update({k: v})
    shipment = cleanDictShip(shipment)
    print("Xml shipment with", len(shipment), "fields imported")
    return shipment


def shipmentFromXml(xml):  # currently hardcoded xml link.... breaks otherwise... how to passfile refs/paths?
    # TODO handle xmls with multiple shipments
    shipment = {}
    newxml = "C:\AmDesp\data\AmShip.xml"
    tree = ET.parse(XMLFILE)
    root = tree.getroot()
    fields = root[0][2]
    # add shipment-wide

    customer = root[0][3].text  # debug

    cat = root[0][0].text
    shipment['category'] = cat
    shipment['deliveryCustomer'] = customer
    for field in fields:
        k = field[0].text
        v = field[1].text
        if v:
            shipment.update({k: v})
    shipment = cleanDictShip(shipment)
    print("Xml shipment with", len(shipment), "fields imported")
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
            shipment.update({'deliveryCustomer': shipment['To Customer']})
            shipment.update({'hireName': shipment['Name']})
            shipment.update({'deliveryAddress': shipment['Delivery Address']})
            shipment = cleanDictShip(shipment)
            manifest.append(shipment)
    print("Manifest imported with ", len(manifest), "shipments\n")
    return manifest


def cleanDictHire(dict):  # if list takes first item!
    # print("Cleaning your shipdict\n")
    newdict = {}
    for k, v in dict.items():
        k = unsanitise(k)
        if v: v = unsanitise(v)
        print("CLEANDICT, unsanitised, keys are:",k," - ",v)
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
        if k == "sendDate":
            v = datetime.strptime(v, '%d/%m/%Y').date()
        newdict.update({k: v})
    else:
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        newdict = {k: v for k, v in newdict.items() if k in hireFields}
        newdict = {k: v for k, v in newdict.items() if k not in expungedFields}
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
        if k == "sendDate":
            v = datetime.strptime(v, '%d/%m/%Y').date()

        newdict.update({k: v})
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        newdict = withoutKeys(newdict, expungedFields)  # in confiig
        newdict.update({k: v})
        # if v: print("UPDATED:",k," - ", v)
    return (newdict)


def hireFromXml(xml):  # currently hardcoded xml link.... breaks otherwise... how to passfile refs/paths?
    # TODO handle xmls with multiple shipments
    hire_dict = {}
    newxml = "C:\AmDesp\data\AmShip.xml"
    tree = ET.parse(XMLFILE)
    root = tree.getroot()
    fields = root[0][2]
    # add shipment-wide

    customer = root[0][3].text  # debug

    cat = root[0][0].text
    for field in fields:
        k = field[0].text
        v = field[1].text
        if v:
            hire_dict.update({k: v})
    hire_dict = cleanDictHire(hire_dict)
    print("Xml hire with", len(hire_dict), "fields imported")
    pprint(hire_dict)
    return hire_dict

def shipmentFromHire():
    pass