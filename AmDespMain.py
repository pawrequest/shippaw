from python.AmDespApp import *


def main():

    app = App()

    app.import_xml()
    app.queue_shipment()
    app.book_collection()

if __name__ == '__main__':
    main()

'''


from python.AmDespClassesApp import *

app = App()
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