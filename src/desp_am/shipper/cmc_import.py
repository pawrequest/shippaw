from pydantic import ConfigDict

from src.desp_am.core.entities import AddressMatch
from src.desp_am.shipper.shipment import ShipmentInput

cust_field_map = dict(
     address_as_str = 'Deliv Address',
     contact_name = 'Deliv Contact',
     email = 'Deliv Email',
     delivery_name = 'Deliv Name',
     postcode = 'Deliv Postcode',
     telephone = 'Deliv Telephone',
)
field_map = dict(
    shipment_name='Name',
    address_as_str='Delivery Address',
    contact_name='Delivery Contact',
    email='Delivery Email',
    delivery_name='Delivery Name',
    postcode='Delivery Postcode',
    telephone='Delivery Telephone',
    customer='To Customer',
    boxes='Boxes',
    send_out_date='Send Out Date',
    send_method='Send Method',
    outbound_id='Outbound ID',
    inbound_id='Inbound ID',
)


def shipment_from_cmc(table, record_name, outbound) -> ShipmentInput:

    ins = {}

    with CmcContext() as cmc:
        transaction = cmc.get_record_with_customer(table, record_name)

        for key, value in field_map.items():
            ins[key] = transaction.get(value)

        return ShipmentInput(
            model_config=ConfigDict(extra='allow'),
            is_dropoff=False,
            is_outbound=outbound,
            category=table,
            remote_address_matched = AddressMatch.NOT,
            **ins
        )
