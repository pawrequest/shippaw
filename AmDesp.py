import sys
import os
import argparse
import pathlib

import suds.transport

from py_code.AmDespShipper import ShippingApp
from py_code.despatchbay.exceptions import ApiException

STORED_XML = "C:\AmDesp\data\Amship.xml"

def shipper(mode, xml_file, sandbox=False):
    app = ShippingApp(sandbox=sandbox)
    app.run(mode=mode, xml_file=xml_file)
    ui = input("Enter to close")
    sys.exit()

if __name__ == '__main__':
    sandbox = False
    # AmDesp called from commandline, i.e launched from Commence
    if len(sys.argv) > 1:
        print(sys.argv)
        mode = sys.argv[1]
        xml_file = sys.argv[2]
        sandbox = True

    # AmDesp called from IDE:
    else:
        # mode = 'ship_out'
        # xml_file = STORED_XML
        # sandbox = True

        mode = 'ship_in'
        xml_file = STORED_XML
        sandbox=True

        # mode = 'track_out'
        # xml_file = STORED_XML
        # sandbox = True
        # #
        # mode = 'track_in'
        # xml_file = STORED_XML
        # sandbox=True


    shipper(mode=mode, xml_file=xml_file, sandbox=sandbox)

# todo [mobility] - repo on ryzen is e/dev/, at amherst is c/paul ... use c/pss on both / all systems? or home?
#  package imports / sys.path etc. amdesp.spec[pathex].now = e/dev
#  add Shipment ID to office db