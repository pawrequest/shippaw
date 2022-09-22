from python.AmDespClasses import *
from python.AmDespFuncs import *

json_exist = False
xml_exist = True

# if json_exist:
#     manifest = manifestFromJson(JSONFILE)
#     for c, shipment in enumerate(manifest):
#         shippies = Shipment(c,shipment)

if json_exist:
    shippies = []
    manifest = manifestFromJson(JSONFILE)

    for c, shipment in enumerate(manifest):
        shippies.append(Shipment(shipment,shipment['id']))
    print("SHIPPIES:",shippies)


if xml_exist:
    shipment = shipmentFromXml(XMLFILE)
    shippy = Shipment(shipment, shipment['customer'])

# print("VARS IN SHIPPY")
# pprint(vars(shippy))

# print ("Shippy", shippy)
# print ("Shippies:",shippies)
for shippy in shippies:
    shippy.CheckBoxes() #shippy =
    shippy.ValDates()
    shippy.ValAddress()
