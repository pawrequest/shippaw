import PySimpleGUI as sg

from despatchbay.exceptions import ApiException
from amdesp.shipment import Shipment
from amdesp.config import get_amdesp_logger

logger= get_amdesp_logger()
def tracking_loop(gui, shipment: Shipment):
    for shipment_id in [shipment.outbound_id, shipment.inbound_id]:
        if shipment_id:
            try:
                gui.tracking_viewer_window(shipment_id=shipment_id)
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
            except Exception as e:
                logger.exception(f"Error while tracking shipment {shipment.shipment_name_printable}: {e}")
            ...
    else:
        return 0