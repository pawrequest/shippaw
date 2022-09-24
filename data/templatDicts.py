## classes ##
## items are a superclass
item_fields = [
    'manufacturer',
    'model',
    'product_type',  # eg radio, megaphone, accessory each has subclass
    'supplier',  # is an organisation
    'stock',
    'buy_price',
    'buy_price_updated', # date field auto updated
    'sell_prices', # a dictionary

]

# radio is an item product_type
radio_fields = [
    'accPort',
    'battery', # class
    'band',
    'charger'  # class
]

# charger is an item product_type
charger_fields = [
    'variant', # eg single, 6way, car
    'suits' # what does it charge? set of items
]

# battery is an item product_type
battery_fields =[
    'suits',
    'voltage',
    'capacity',
    'belt_clip',
    'charged_by'
]


## prices
price_fields = [
    'abs_min_price',
    'sinlge_price',
    'buy_6_price',
]

## objects ##
# PD705 is a [Radio]
PD705 = {
    'maanufacturer': 'Hytera',
    'model': 'PD705',
    'product_type': 'radio',
    'supplier': 'syndico',  #
    'stock': '200',
    'accPort': 'prop-pd705',
    'battery': 'BC2008',
    'band': 'uhf'
}

person_fields = ['name', 'phone']
# phone = dict eg {'mobile' : 077664646587, 'office':5357435}


RADIOBINS = {'A66' : "somepath"}