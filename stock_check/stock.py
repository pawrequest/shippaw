from datetime import datetime, timedelta
from dataclasses import dataclass
from core.funcs import powershell_runner




date_range = 3
temp_file = 'temp_file.json'

stock_change = {}



def get_dates(n):
    return [datetime.today() + timedelta(days=i) for i in range(n + 1)]


def get_hires_out(date):
    hires_out = ''
    return hires_out

def radios_out(hire):
    radio_type = 'hytera'
    num_radios = 3
    return radio_type, num_radios


dates = get_dates(date_range)
for date in dates:
    hires_out = get_hires_out(date)
    for hire in hires_out:
        radio_type, radio_num = radios_out(hire)
        stock_change[radio_type] = stock_change.get(radio_type, 0) - radio_num
        ...

...



powershell_runner()

...

