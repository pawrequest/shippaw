# todo updates commence when shipment delivered
# imports in-range shipments to batch process

import sys
from amdesp.shipper import App, get_shipments, get_sender_recip
from amdesp.config import Config
from bench.gui import Gui
from amdesp.gui_layouts import GuiLayout, tracking_viewer_window

STORED_XML = r"C:\Users\Surface\PycharmProjects\AmDesp\data\AmShip.xml"
SANDBOX = None


def shipper():
    """ sandbox = fake shipping client, no money for labels!"""
    config = Config()
    client = config.get_dbay_client(sandbox=SANDBOX)
    app = App()
    # app.setup_commence(config)
    gui = Gui()
    layout = GuiLayout()
    shipments = get_shipments(in_file=in_file, config=config)
    for shipment in shipments:
        if 'ship' in mode:
            if 'in' in mode:
                shipment.is_return = True
            shipment.sender, shipment.recipient = get_sender_recip(shipment, client=client)
            app.gui_ship(client=client, config=config, shipment=shipment, sandbox=SANDBOX)
        elif 'track' in mode:
            if 'in' in mode:
                try:
                    tracking_viewer_window(shipment_id=shipment.inbound_id, client=client)
                except:
                    ...
                    # sg.popup_error("No Shipment ID")

            elif 'out' in mode:
                try:
                    tracking_viewer_window(shipment.outbound_id, client=client)
                except:
                    ...
                    # sg.popup_error("No Shipment ID")


if __name__ == '__main__':
    # AmDesp called from commandline, i.e launched from Commence
    if len(sys.argv) > 1:
        print(sys.argv)
        mode = sys.argv[1]
        in_file = sys.argv[2]
        SANDBOX = True

    # AmDesp called from IDE:
    else:
        # mode = 'ship_in'
        # xml_file = STORED_XML
        # SANDBOX = True

        mode = 'ship_out'
        in_file = STORED_XML
        SANDBOX = True

        # mode = 'track_out'
        # xml_file = STORED_XML
        # SANDBOX = True
        # #
        # mode = 'track_in'
        # xml_file = STORED_XML
        # SANDBOX=True

    shipper()

# todo [mobility] - repo on ryzen is e/dev/, at amherst is c/paul ... use c/pss on both / all systems? or home?
#  package imports / sys.path etc. amdesp.spec[pathex].now = e/dev
#  add Shipment ID fields, package delivered field, ship/track buttons to office db


# mode = 'track_out'
# xml_file = STORED_XML
# sandbox = True
# #
# mode = 'track_in'
# xml_file = STORED_XML
# sandbox=True

# mode = 'ship_out'
# xml_file = STORED_XML
# sandbox = True
