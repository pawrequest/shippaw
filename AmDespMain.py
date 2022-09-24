from python.AmDespClasses import *
from python.AmDespFuncs import *
# mode = ""
# shipment = shipmentFromXml(XMLFILE)
# shippy = Shipment(shipment, 12)
# shippy.ProcessShipment()
# hire = hireFromXml(XMLFILE)
# herman = Shipment(hire, 32)
# herman.ship()
#
# Shippy = XmlToShippy(XMLFILE)
#
#

if sys.argv:
    print(sys.argv[0])
    xmlfile = sys.argv[0]
else:
    xmlfile=XMLFILE



hiredict = hire_from_xml(XMLFILE)
oHire = Hire(hiredict)
oHire.ship_hire()


# ship_hire(hiredict)
