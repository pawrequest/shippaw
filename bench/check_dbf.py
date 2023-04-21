from dbfread import DBF
dbase_file = r'R:\paul_notes\pss\AmDesp\data\amherst_hire.dbf'


for record in DBF(dbase_file):
    [print(f'{k} : {v}') for k,v in record.items()]
