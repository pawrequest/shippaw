

def tracking_loop(ship_ids):
    for shipment_id in ship_ids:
        shipment_return = CLIENT.get_shipment(shipment_id).is_delivered


def track(shipments):
    for shipment in shipments:
        if ship_ids := [shipment.outbound_id, shipment.inbound_id]:
            try:
                tracking_loop(ship_ids=ship_ids)
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