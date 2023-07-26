import PySimpleGUI as sg
from despatchbay.despatchbay_entities import ShipmentReturn

from despatchbay.exceptions import ApiException

from shipper.shipment import Shipment
from core.config import logger




def tracking_viewer_window(self, client, shipment_return:ShipmentReturn):
    delivered = shipment_return.is_delivered
    tracking_numbers = [parcel.tracking_number for parcel in shipment_return.parcels]
    tracking_d = {}
    layout = []
    for tracked_parcel in tracking_numbers:
        parcel_layout = []
        signatory = None
        params = {}
        tracking = client.get_tracking(tracked_parcel)
        # courier = tracking['CourierName'] # debug unused?
        # parcel_title = [f'{tracked_parcel} ({courier}):'] # debug unused?
        history = tracking['TrackingHistory']
        for event in history:
            if 'delivered' in event.Description.lower():
                signatory = f"{chr(10)}Signed for by: {event.Signatory}"
                params.update({'background_color': 'aquamarine', 'text_color': 'maroon4'})

            event_text = sg.T(
                f'{event.Date} - {event.Description} in {event.Location}{signatory if signatory else ""}',
                **params)

            parcel_layout.append([event_text])

        parcel_col = sg.Column(parcel_layout)
        layout.append(parcel_col)
        tracking_d.update({tracked_parcel: tracking})

    shipment_return.tracking_dict = tracking_d
    tracking_window = sg.Window('', [layout])
    tracking_window.read()