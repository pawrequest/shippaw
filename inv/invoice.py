from typing import Annotated

from dbfread import DBF, DBFNotFound
import pandas as pd
from pydantic import BaseModel, BeforeValidator


def commence_string(in_string: str):
    if '\x00' in in_string:
        in_string = in_string.split('\x00')[0]
    out_string = in_string.replace('\r\n', '\n')
    return out_string


MyStr = Annotated[str, BeforeValidator(commence_string)]


prices_wb = r'C:\paul\office_am\invoice\prices.xlsx'


prices = pd.read_excel(prices_wb)
# order = pd.read_csv('C:\paul\office_am\invoice\hire_i.TXT', sep=',', header=1)
order1 = [i for i in DBF('C:\paul\office_am\invoice\hire_i.dbf')][0]
order2 = DBF('C:\paul\office_am\invoice\hire_i.dbf', load=True)
order = {i:k for i,k in order1.items() if k}
order_items = {}
for field, qty in order.items():
    if field[0:3].lower() == 'inv':
        order_items[field[4:]] = qty.strip('\x00')

...

class Order(BaseModel):
    ...
