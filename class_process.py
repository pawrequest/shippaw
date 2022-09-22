from python.ADFuncs import *

json_exist = True
xml_exist = True

# if json_exist:
#     manifest = manifestFromJson(JSONFILE)
#     for c, shipment in enumerate(manifest):
#         shippies = Shipment(c,shipment)

# if json_exist:
#     shippies = []
#     manifest = manifestFromJson(JSONFILE)
#
#     for c, shipment in enumerate(manifest):
#         shippies.append(Shipment(shipment,shipment['id']))
#     print("SHIPPIES:",shippies)


if xml_exist:
    shipment = shipmentFromXml(XMLFILE)
    shippy = Shipment(shipment, 1)

print("VARS IN SHIPPY")
# pprint(vars(shippy))

print ("Shippy", shippy)
# print ("Shippies:",shippies)
# can't check boxes until parse address
# shippy = shippy.CheckBoxes()
