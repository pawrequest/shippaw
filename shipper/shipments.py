from core.config import logger
from core.enums import ShipmentCategory
from shipper.shipment import get_valid_shipment, shipdict_from_record


def shipments_from_records(category: ShipmentCategory, import_map: dict, outbound: bool, records: [dict]):
    shipments = []
    for record in records:
        [logger.debug(f'INPUT RECORD - {k} : {v}') for k, v in record.items()]
        try:
            ship_dict = shipdict_from_record(outbound=outbound, record=record,
                                             category=category, import_mapping=import_map)
            shipments.append(get_valid_shipment(input_dict=ship_dict))

        except Exception as e:
            logger.exception(f'SHIPMENT CREATION FAILED: {record.__repr__()} - {e}')
            continue

    return shipments
