import json
import xml.etree.ElementTree as ET

from config import *


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
            shipment.update({k:v})
    shipment=cleanDict(shipment)
    print("Xml shipment with",len(shipment),"fields imported")
    return shipment

def manifestFromJson(manifest_list_dict):
    print("Parsing Json")
    manifest = []
    with open(manifest_list_dict) as f:
        json_data = json.load(f)
        cat = json_data['CommenceCategory']
        manifest_data = json_data['Items']
        for shipment in manifest_data:
            # newship = {}
            shipment.update({'category': cat})
            shipment.update({'customer': shipment['To Customer']})
            shipment.update({'hireName':shipment['Name']})
            shipment = cleanDict(shipment)
            shipment
            manifest.append(shipment)
    print("Manifest imported with ", len(manifest), "shipments")
    return manifest


def cleanDict(dict):  # if list takes first item!
    print("Cleaning your dict")
    newdict={}
    for k, v in dict.items():
        if k in com_fields: k = com_fields[k]
        k = toCamel(k)
        if isinstance(v,list):
            v = v[0]
        if v.replace(",","").isnumeric() and int(v.replace(',','')) == 0:
            v = None
        elif v.isalnum():
            v = v.title()
        newdict = {k: v for k, v in newdict.items() if v is not None and v not in ['', 0]}
        newdict = withoutKeys(newdict, expungedFields)
        newdict.update({k:v})
    return(newdict)



