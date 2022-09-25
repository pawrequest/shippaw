from python.AmDespClasses import *
from python.AmDespFuncs import *

if sys.argv:
    print(sys.argv[0])
    xmlfile = sys.argv[0]
else:
    xmlfile=CONFIG_PATH['XMLFILE']

##########################################
# working
hiredict = hire_from_xml(CONFIG_PATH['XMLFILE'])
oHire = Hire(hiredict)
oHire.ship_hire()
ship_hire(hiredict)
##########################################
# pd = radios_dict['PD705']
# # pro = Product()
# rad=Radio(pd)
# print (rad)



# todo: makes objects from list on file