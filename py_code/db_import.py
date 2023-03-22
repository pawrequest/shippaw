import pathlib
from pprint import pprint

from dbfread import DBF
datapath = pathlib.Path(r'E:\Dev\AmDesp\data\shipping_candidates.dbf')

dbf_file = DBF(datapath)
for record in dbf_file:
    pr
# print(next(data.records))

class CmcImport:
    def __init__(self, data):
        self.name = None
        self.send_out = None
        self.delivery_a= None
        self.delivery_c=None
        self.delivery_d = None
        self.delivery_n = None
        self.delivery_p= None
        self.delivery_r = None
        self.boxes = None
        self.send___col= None
        self.send_metho= None
        self.shipment_i= None
        self.status = None
        for k, record in data:
            setattr(self,k,record)

records =[]
for record in (dbf_file.records):
    pprint (record)
    records.append(CmcImport(record))
...
