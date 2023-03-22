import pathlib
from pprint import pprint

from dbfread import DBF

datapath = pathlib.Path(r'E:\Dev\AmDesp\data\shipping_candidates.dbf')

dbf_file = DBF(datapath)

class CmcImport:


exported = []
for record in (dbf_file.records):
    pprint(record)
    obj = CmcImport(record)
    exported.append(CmcImport(record))
...
