class Shipment():
    def __init__(self):
        self.id = 0
        self.customer = "" # shipment_dict['customer']
        self.phone = 0 # shipment_dict[phone]
        self.email = "" # shipment_dict[email]
        self.boxes = 0 # shipment_dict[boxes]
        self.send_date = "" # shipment_dict[send_date]
        # self.address = "" # shipment_dict[address]
        self.postcode = "" # shipment_dict[postcode]
        self.building_num = None
        self.firstline = None
        self.address_object = None
        self.date_object = None
        self.service_object = None
        self.shipped_object = None
        self.added_object = None
        self.despatch_address_key = None
        self.is_shipped = None
        self.shipping_service_id = 101


# powershell -noexit -file C:\paul\AmDesp\python\test.ps1