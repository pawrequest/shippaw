from python.AmDespApp import ShippingApp
from python.Programmer import ProgrammingAssistant


def main():

    app = ShippingApp()

    app.xml_to_shipment()
    if app.queue_shipment():
        app.book_collection()
    app.log_json()


def programmer():
    prog = ProgrammingAssistant()
    prog.BootUp()
    ...

def vbtest():
    print ("SOMETHNG")
if __name__ == '__main__':
    main()
    # vbtest()
    # programmer()

'''


from python.AmDespClassesApp import *

app = ShippingApp()
app.make_hire_shipment()
app.queue_shipment()
app.book_collection()


if sys.argv:
    print(sys.argv[0])
    xmlfile = sys.argv[0]
else:
    xmlfile=CONFIG_PATH['XMLFILE']
'''

'''
# pre-app
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
'''






# todo: makes objects from list on file