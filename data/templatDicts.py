## classes ##
## items are a superclass
item_fields = [
    'manufacturer',
    'model',
    'product_type',  # eg radio, megaphone, accessory each has subclass
    'supplier',  # is an organisation
    'buy_price',
    'buy_price_updated', # date field auto updated
    'sell_prices', # a dictionary

]

product_types = ['Radio','Megaphone','charger','battery','audioAcc']

# radio is an item product_type
radio_fields = [
    'accPort',
    'battery', # class
    'band',
    'charger' # is a class
    'variant' # fuck you hytera
    'cps' # programming software
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

# audioAcc is an item
audioAcc_fields = ['suits', 'format', 'accPort']

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

## people
person_fields = [
    'name',
    'phone', # dict of 'tel_type' : 07864654465 etc
    'email'

]

## organisations
org_fields = []

# inventoryItem is an individual physical object
invenItem_fields = [
    'serial',
    'owner',
    'our_purchase_date'
    'our_sale_date'
]


# codeplug
codeplug_fields = [
    'customer',
    'radio',
    'channels' # dict of channel info

]