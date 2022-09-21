from python.ADFuncs import *

json_exist = True
xml_exist = True

if json_exist:
    manifest = manifestFromJson(JSONFILE)

if xml_exist:
    shipment = shipmentFromXml(XMLFILE)
    # pprint(shipment)



# for c, shipment in enumerate(manifest):
#     shippy = Shipment(c,shipment)
#
# print("VARS IN SHIPPY")
# pprint(vars(shippy))
# for k,v in vars(objship):
#     if v:
#         print(k,v)
