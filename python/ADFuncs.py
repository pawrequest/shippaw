import xml.etree.ElementTree as ET

from config import *


def unsanitise(string):
    # string = string.replace("&amp;", chr(38)).replace("&quot;", chr(34)).replace("&apos;", chr(39)).replace("&lt;",
    #                                                                                                         chr(60)).replace(
    #     "&gt;", chr(62)).replace("&gt;", chr(32)).replace("&#", "").replace(";", "").replace(",", "")
    # return string
    string = string.replace("&amp;", chr(38))
    string = string.replace("&quot;", chr(34))
    string = string.replace("&apos;", chr(39))
    string = string.replace("&lt;", chr(60))
    string = string.replace("&gt;", chr(62))
    string = string.replace("&gt;", chr(32))
    string = string.replace("&#", "")
    string = string.replace(";", "")
    return string

def shipmentFromXml(xml):
    shipment = {}
    newxml = "C:\AmDesp\data\AmShip.xml"
    # print(XMLFILE)
    tree = ET.parse(XMLFILE)
    root = tree.getroot()
    fields = root[0][2]

    # add shipment-wide
    customer = root[0][3][1][0][0].text
    cat = root[0][0].text
    shipment['category'] = cat
    shipment['customer'] = customer
    for field in fields:
        # keys
        k = field[0].text
        # k = unsanitise(k) # unnecessary, maybe ET does it?
        k = toPascal(k)

        # values
        v = field[1].text
        if v:
            # v = unsanitise(v) # unncessary?
            v = v.title()
        if v == "0":
            v = False

        shipment.update({k : v})
    return shipment

def manifestFromJson(data):
    # is json or xml?
    manifest = []
    datatype = "json"
    import json
    if datatype == "json":
        with open(str(data)) as f:
            json_data = json.load(f)
            cat = json_data['CommenceCategory']
            manifest = json_data['Items']
            for id, shipment in enumerate(manifest):
                new_ship = {}
                shipment['category'] = cat
                shipment['customer'] = shipment['To Customer']
                for k, v in shipment.items():
                    if type(v) == list:
                        v=v[0]
                    if k in com_fields:
                        k = com_fields[k]
                    if k in field_fixes:
                        k = field_fixes[k]
                    k = toPascal(k)
                    v = v.title()
                    new_ship.update({k: v})
    return manifest


