from pprint import pprint

from python.ADFuncs import *
from python.shipment_class import *

# shipment = shipmentFromXml(XMLFILE)
manifest = manifestFromJson(JSONFILE)
for c, shipment in enumerate(manifest):
    shippy = Shipment(c,shipment)

print("SHIPPY")
pprint(vars(shippy))

# for k,v in vars(objship):
#     if v:
#         print(k,v)
