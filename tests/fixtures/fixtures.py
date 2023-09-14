import datetime
from collections import OrderedDict

record_hire = OrderedDict([
    ('NAME', 'Test - 16/08/2023 ref 31619'),
    ('DELIVERY_A', '30 bennet close\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_C', 'Test\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_E', 'dsgdsa@dasgdg.com\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_P', 'ME8 8SP\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_T', '07666 666666'),
    ('DELIVERY_N', 'Test\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('BOXES', '1'),
    ('STATUS', 'Quote given'),
    ('FIELD10', 'Test\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('SEND_OUT_D', datetime.date(2023, 8, 21)),
    ('INBOUND_ID', None),
    ('OUTBOUND_I', '100786-6341\r\n100786-6340\r\n100786-6336\x00'),
    ('CUSTOMER_N', None),
    ('DB_LABEL_P', True),
    ('REPROGRAMM', False),
    ('SENDING_ST', 'Fine no problem')])

record_hire_bad_postcode = OrderedDict([
    ('NAME', 'Test - 16/08/2023 ref 31619'),
    ('DELIVERY_A', '30 bennet close\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_C', 'Test\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_E', 'dsgdsa@dasgdg.com\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_P', 'ME8 SP\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_T', '07666 666666'),
    ('DELIVERY_N', 'Test\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('BOXES', '1'),
    ('STATUS', 'Quote given'),
    ('FIELD10', 'Test\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('SEND_OUT_D', datetime.date(2023, 8, 21)),
    ('INBOUND_ID', None),
    ('OUTBOUND_I', '100786-6341\r\n100786-6340\r\n100786-6336\x00'),
    ('CUSTOMER_N', None),
    ('DB_LABEL_P', True),
    ('REPROGRAMM', False),
    ('SENDING_ST', 'Fine no problem')])


record_sale = OrderedDict([
    ('NAME', 'Woodlands Primary School - 01/09/2023 ref 313'),
    ('DELIVERY_A', 'Higham School Road\r\nTonbridge\r\nKent\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_C', 'Kellie Tait\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_E', 'finance@woodlands.kent.sch.uk\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_N', 'Woodlands Primary School\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_P', 'TN10 4BB\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('DELIVERY_T', '01732 355577'),
    ('OUTBOUND_I', '100786-21454583\x00\x00\x00\x00\x00\x00\x00\x00'),
    ('FIELD9', 'Woodlands Primary School\x00')])

