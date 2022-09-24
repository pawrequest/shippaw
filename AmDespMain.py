from config import *
from python.AmDespClasses import *
from python.AmDespFuncs import *

if sys.argv:
    print(sys.argv[0])
    xmlfile = sys.argv[0]
else:
    xmlfile=XMLFILE

##########################################
## working
# hiredict = hire_from_xml(XMLFILE)
# oHire = Hire(hiredict)
# oHire.ship_hire()
# ship_hire(hiredict)
##########################################

pro = Product()
rad=Radio(PD705)


