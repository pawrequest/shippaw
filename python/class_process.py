from config import *
from shipment_class import Shipment

shipment =[]

for x in range(5):
    shipment.append(Shipment(x))
print (shipment)