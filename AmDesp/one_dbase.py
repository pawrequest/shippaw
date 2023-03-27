class Amherst_one_dbase:
    def __init__(self, data, is_return=False):
        self.shipment_name = data['NAME'].split('\x00')[0]
        self.date = data['SEND_OUT_D']
        self.address = data['DELIVERY_A'].split('\x00')[0]
        self.name = data['DELIVERY_C'].split('\x00')[0]  # contact
        self.company_name = data['DELIVERY_N'].split('\x00')[0]
        self.postcode = data['DELIVERY_P'].split('\x00')[0]
        self.boxes = data['BOXES']
        self.status = data['STATUS']
        self.email = data['DELIVERY_E'].split('\x00')[0]
        # different fieldnames at home vs at work...
        self.telephone = data['DELIVERY_T'].split('\x00')[0]
        if data['FIELD10']:
            self.customer = data['FIELD10'].split('\x00')[0]
        elif data['FIELD17']:
            self.customer = data['FIELD10'].split('\x00')[0]
        else:
            print("Customer fieldname is neither FIELD10 nor FIELD17 in Commence export DBase")
        self.is_return = is_return
        try:
            self.id_inbound = data['ID_INBOUND']
            self.id_outbound = data['ID_OUTBOUND']
        except:
            ...
        self.service = None
        self.sender = None
        self.recipient = None
        self.parcels = None
        self.collection_booked = False
