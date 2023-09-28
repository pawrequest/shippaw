import datetime
from collections import OrderedDict

RECORDS_DICT = dict(
    hire=[OrderedDict([('NAME', 'Test Customer - 30/09/2022 ref 29372'),
                       ('DELIVERY_A', '20 bennet close\r\nwelling\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_C', 'A Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_E', 'admin@amherst.co.uk\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_P', 'DA16 3HU\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_T', '020 7328 9792'),
                       ('DELIVERY_N', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'), ('BOXES', '1'),
                       ('STATUS', 'Returned all OK'),
                       ('FIELD10', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00\x00'), ('DELIVERY_R', None),
                       ('INBOUND_ID', '100786-6312\r\n100786-6314\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('OUTBOUND_I', '100786-6315\x00'), ('REPROGRAMM', False),
                       ('SENDING_ST', 'Fine no problem')])],

    sale=[OrderedDict([('NAME', 'Test Customer - 14/11/2022 ref 34'), (
        'DELIVERY_A', '25 Castle Street \r\nBarnstaple \r\nDevon\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_C', 'Fred Smith\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_E', 'prosodyspeaks@gmail.com\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_N', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_P', 'DA16 3HU\x00\x00\x00\x00\x00\x00\x00\x00'),
                       ('DELIVERY_T', '07878 867844'),
                       ('OUTBOUND_I', None), ('FIELD9', 'Test Customer\x00')])],

    customer=[OrderedDict(
        [('ADDRESS', '25 Castle Street \r\nBarnstaple \r\nDevon\x00\x00\x00\x00\x00\x00\x00\x00'),
         ('CONTACT_NA', 'Fred Smith\x00\x00\x00\x00\x00\x00\x00\x00'),
         ('DELIV_ADDR', '20 bennet close\x00\x00\x00\x00\x00\x00\x00\x00'),
         ('DELIV_CONT', 'Fred Smith\x00\x00\x00\x00\x00\x00\x00\x00'),
         ('DELIV_EMAI', 'prosodyspeaks@gmail.com\x00\x00\x00\x00\x00\x00\x00\x00'),
         ('DELIV_NAME', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'), ('DELIV_POST', 'DA16 3HU\x00'),
         ('DELIV_TELE', '07878 867844'), ('NAME', 'Test Customer')])],

    bulk=[
        OrderedDict([
            ('NAME', 'Bovingdons - 09/10/2023 ref 20071'), ('DELIVERY_A', '1 bennett close'),
            ('DELIVERY_C', 'Test person 1'),
            ('DELIVERY_E', 'admin@amherst.co.uk'), ('DELIVERY_P', 'da163hu'), ('DELIVERY_T', '020 8874 8032'),
            ('DELIVERY_N', 'Bovingdons'), ('BOXES', '1'), ('STATUS', 'Booked in'), ('FIELD10', 'Bovingdons\x00'),
            ('SEND_OUT_D', datetime.date(2023, 10, 9)), ('INBOUND_ID', None), ('OUTBOUND_I', None),
            ('CUSTOMER_N', None),
            ('DB_LABEL_P', False), ('REPROGRAMM', False), ('SENDING_ST', 'Fine no problem')]),

        OrderedDict([
            ('NAME', 'Eynsford Running Club - 10/10/2023 ref 20157'), ('DELIVERY_A', '2 bennett close'),
            ('DELIVERY_C', 'Test person 2'), ('DELIVERY_E', 'admin@amherst.co.uk'), ('DELIVERY_P', 'da163hu'),
            ('DELIVERY_T', '07860 840932'), ('DELIVERY_N', 'Eynsford Running Club'), ('BOXES', '1'),
            ('STATUS', 'Booked in'),
            ('FIELD10', 'Eynsford Running Club\x00'), ('SEND_OUT_D', datetime.date(2023, 10, 10)), ('INBOUND_ID', None),
            ('OUTBOUND_I', None), ('CUSTOMER_N', None), ('DB_LABEL_P', False), ('REPROGRAMM', False),
            ('SENDING_ST', 'Fine no problem')]),

        OrderedDict([
            ('NAME', 'Ilkley Literature Festival - 02/10/2023 ref 20196'), ('DELIVERY_A', '3 bennett close'),
            ('DELIVERY_C', 'Test person 3'), ('DELIVERY_E', 'admin@amherst.co.uk'), ('DELIVERY_P', 'da163hu'),
            ('DELIVERY_T', '01943 601210'), ('DELIVERY_N', 'Ilkley Literature Festival'), ('BOXES', '1'),
            ('STATUS', 'Booked in'), ('FIELD10', 'Ilkley Literature Festival\x00'),
            ('SEND_OUT_D', datetime.date(2023, 10, 2)),
            ('INBOUND_ID', None), ('OUTBOUND_I', None), ('CUSTOMER_N', None), ('DB_LABEL_P', False),
            ('REPROGRAMM', False),
            ('SENDING_ST', 'Fine no problem')]),

        OrderedDict([
            ('NAME', 'REB Limited - 06/09/2023 ref 20188'), ('DELIVERY_A', '4 bennett close'),
            ('DELIVERY_C', 'Test person 4'),
            ('DELIVERY_E', 'admin@amherst.co.uk'), ('DELIVERY_P', 'da163hu'), ('DELIVERY_T', '07725 816910'),
            ('DELIVERY_N', 'REB Limited'), ('BOXES', '1'), ('STATUS', 'Booked in'), ('FIELD10', 'REB Limited\x00'),
            ('SEND_OUT_D', datetime.date(2023, 10, 6)), ('INBOUND_ID', None), ('OUTBOUND_I', None),
            ('CUSTOMER_N', None),
            ('DB_LABEL_P', False), ('REPROGRAMM', False), ('SENDING_ST', 'Fine no problem')]),

        OrderedDict([
            ('NAME', 'Trampoline League - 11/10/2023 ref 31247'), ('DELIVERY_A', '5 bennett close'),
            ('DELIVERY_C', 'Test person 5'), ('DELIVERY_E', 'admin@amherst.co.uk'), ('DELIVERY_P', 'da163hu'),
            ('DELIVERY_T', '07845 419917'), ('DELIVERY_N', 'Trampoline League'), ('BOXES', '2'),
            ('STATUS', 'Booked in'),
            ('FIELD10', 'Trampoline League\x00'), ('SEND_OUT_D', datetime.date(2023, 10, 9)), ('INBOUND_ID', None),
            ('OUTBOUND_I', None), ('CUSTOMER_N', None), ('DB_LABEL_P', False), ('REPROGRAMM', False),
            ('SENDING_ST', 'Fine no problem')])
    ]
)
