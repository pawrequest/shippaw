from config import *
from python.AmDespClasses import *
from python.AmDespFuncs import *

# shippies = JsonToShippies(JSONFILE)
# for shippy in shippies:
#     shippy.CheckBoxes() #shippy =
#     shippy.ValDates()
#     shippy.ValAddress()
shipment = shipmentFromXml(XMLFILE)
shippy = Shipment(shipment,12)
print (shippy)