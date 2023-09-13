from collections import OrderedDict

record_sale = OrderedDict([('NAME', 'Test Customer - 14/11/2022 ref 34'),
                           ('DELIVERY_A', '25 Castle Street \r\nBarnstaple \r\nDevon\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_C', 'Fred Smith\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_E', 'prosodyspeaks@gmail.com\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_N', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_P', 'DA16 3HU\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_T', '07878 867844'),
                           ('OUTBOUND_I', None),
                           ('FIELD9', 'Test Customer\x00')])

record_hire = OrderedDict([('NAME', 'Test Customer - 30/09/2022 ref 29372'),
                           ('DELIVERY_A', '20 bennet close\r\nwelling\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_C', 'A Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_E', 'admin@amherst.co.uk\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_P', 'DA16 3HU\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_T', '020 7328 9792'),
                           ('DELIVERY_N', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('BOXES', '1'),
                           ('STATUS', 'Returned all OK'),
                           ('FIELD10', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('DELIVERY_R', None),
                           ('INBOUND_ID', '100786-6312\r\n100786-6314\x00\x00\x00\x00\x00\x00\x00\x00'),
                           ('OUTBOUND_I', '100786-6315\x00'),
                           ('REPROGRAMM', False),
                           ('SENDING_ST', 'Fine no problem')])

record_customer = OrderedDict([('ADDRESS', '25 Castle Street \r\nBarnstaple \r\nDevon\x00\x00\x00\x00\x00\x00\x00\x00'),
                               ('CONTACT_NA', 'Fred Smith\x00\x00\x00\x00\x00\x00\x00\x00'),
                               ('DELIV_ADDR', '20 bennet close\x00\x00\x00\x00\x00\x00\x00\x00'),
                               ('DELIV_CONT', 'Fred Smith\x00\x00\x00\x00\x00\x00\x00\x00'),
                               ('DELIV_EMAI', 'prosodyspeaks@gmail.com\x00\x00\x00\x00\x00\x00\x00\x00'),
                               ('DELIV_NAME', 'Test Customer\x00\x00\x00\x00\x00\x00\x00\x00'),
                               ('DELIV_POST', 'DA16 3HU\x00'), ('DELIV_TELE', '07878 867844'),
                               ('NAME', 'Test Customer')])
