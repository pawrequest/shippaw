from config import *

class Shipment:
    def __init__(self, shipment_dict):
        self.id = 0
        self.customer = shipment_dict['customer']
        self.phone = shipment_dict['phone']
        self.email = shipment_dict['email']
        self.boxes = shipment_dict['boxes']
        self.send_date = shipment_dict['send_date']
        self.crapstring = shipment_dict['commence_address']
        self.postcode = shipment_dict['postcode']
        self.building_num = False
        self.firstline = False
        self.address_object = False
        self.date_object = False
        self.service_object = False
        self.shipped_object = False
        self.added_object = False
        self.despatch_address_key = False
        self.is_shipped = False
        self.shipping_service_id = 101


# powershell -noexit -file C:\paul\AmDesp\python\ps_test.ps1