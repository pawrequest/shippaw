from pprint import pprint

from dateutil.parser import parse
from datetime import datetime

import PySimpleGUI as sg
from .gui_layouts import GuiLayout


class AmdespGui:
    def __init__(self, shipment):
        self.shipment = shipment
        self.layouts = GuiLayout(self)

    def run(self):
        sg.theme('Dark Blue')

        ## get a layout
        # layout = self.layouts.main_window()

        window = self.layouts.main_window()

        while True:
            event, values = window.read()
            pprint(values.items())
            if event in (sg.WINDOW_CLOSED, 'Exit'):
                break
            if event == '-GO-':
                shipment = self.shipment
                self.book_collection(
                    service_id=shipment.service.service_id,
                    parcels=shipment.parcels,
                    client_reference=shipment.label_text,
                    collection_date=shipment.date,
                    sender_address=shipment.sender,
                    recipient_address=shipment.recipient,
                    follow_shipment=True
                )
        window.close()

    def book_collection(self, **shipment_details):
        shipment = self.shipment
        client = shipment.CNFG.client
        shipment_request = client.shipment_request(**shipment_details)
        if shipment.is_return:
            shipment.shipment_id_inbound = client.add_shipment(shipment_request)
            shipment_id = shipment.shipment_id_inbound
        else:
            shipment.shipment_id_outbound = client.add_shipment(shipment_request)
            shipment_id = shipment.shipment_id_outbound
        shipment_return = client.book_shipments(shipment_id)[0]  # debug there could be more than one here??

        shipment.collection_booked = True

        # save label
        label_pdf = client.get_labels(shipment_return.shipment_document_id, label_layout='2A4')
        try:
            label_string = f"{shipment.customer} - {str(shipment.date.date)}.pdf"
        except:
            label_string = f"{shipment.shipment_name}.pdf"
        label_pdf.download(shipment.CNFG.label_dir / label_string)
        shipment.label_location = str(shipment.CNFG.label_dir / label_string)

        shipment.timestamp = f"{datetime.now().isoformat(sep=' ', timespec='seconds')}"
        print(
            f"\nCollection has been booked for {shipment.customer} on {shipment.date.date} "
            f"\nLabel downloaded to {shipment.label_location}.")
        return True

    def print_label(self):
        ...

    def update_commence(self):
        ...
    def log_shipment(self):
        ...
    def email_label(self):
        ...
