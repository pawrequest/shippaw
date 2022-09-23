from python.AmDespClasses import *
from python.AmDespFuncs import *

# shipment = shipmentFromXml(XMLFILE)
# shippy = Shipment(shipment, 12)
# shippy.ProcessShipment()
hire = hireFromXml(XMLFILE)
herman = HireShipment(hire, 32)
herman.Ship()

