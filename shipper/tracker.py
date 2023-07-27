import PySimpleGUI as sg
from despatchbay.exceptions import ApiException

import shipper.shipper
from core.config import logger


def tracking_loop(ship_ids):
    for shipment_id in ship_ids:
        client = shipper.shipper.DESP_CLIENT
        shipment_return = client.get_shipment(shipment_id).is_delivered

#
# def track(shipments):
#     for shipment in shipments:
#         if ship_ids := [shipment.outbound_id, shipment.inbound_id]:
#             try:
#                 tracking_loop(ship_ids=ship_ids)
#             except ApiException as e:
#                 if 'no tracking data' in e.args.__repr__().lower():
#                     logger.exception(f'No Tracking Data for {shipment.shipment_name_printable}')
#                     sg.popup_error(f'No Tracking data for {shipment.shipment_name_printable}')
#                 if 'not found' in e.args.__repr__().lower():
#                     logger.exception(f'Shipment {shipment.shipment_name_printable} not found')
#                     sg.popup_error(f'Shipment ({shipment.shipment_name_printable}) not found')
#
#                 else:
#                     logger.exception(f'ERROR for {shipment.shipment_name_printable}')
#                     sg.popup_error(f'ERROR for {shipment.shipment_name_printable}')

def track2(shipments):
    for shipment in shipments:
        if ship_ids := [shipment.outbound_id, shipment.inbound_id]:
            for id in ship_ids:
                try:
                    event, values = get_tracking(shipment_id=id).read()
                except ApiException as e:
                    if 'no tracking data' in e.args.__repr__().lower():
                        logger.exception(f'No Tracking Data for {shipment.shipment_name_printable}')
                        sg.popup_error(f'No Tracking data for {shipment.shipment_name_printable}')
                    if 'not found' in e.args.__repr__().lower():
                        logger.exception(f'Shipment {shipment.shipment_name_printable} not found')
                        sg.popup_error(f'Shipment ({shipment.shipment_name_printable}) not found')

                    else:
                        logger.exception(f'ERROR for {shipment.shipment_name_printable}')
                        sg.popup_error(f'ERROR for {shipment.shipment_name_printable}')


def get_tracking(shipment_id):
    client = shipper.shipper.DESP_CLIENT
    shipment_return = client.get_shipment(shipment_id)
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
                event_text = sg.T(
                    f'{event.Date} - {event.Description} in {event.Location}{signatory}',
                    background_color='green', text_color='white')

            else:
                event_text = sg.T(
                    f'{event.Date} - {event.Description} in {event.Location}',
                    **params)

            parcel_layout.append([event_text])

        parcel_col = sg.Column(parcel_layout)
        layout.append(parcel_col)
        tracking_d.update({tracked_parcel: tracking})

    shipment_return.tracking_dict = tracking_d
    return sg.Window('', [layout])
