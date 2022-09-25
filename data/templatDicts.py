from pyexcel_ods3 import get_data
## classes ##




radios_dict = dict()
# radiosdict = {"PD705":{"MANU":"HYT","PRICE":100}}

radios_dict = {'PD705':
    {
        'manufacturer': 'Hytera',
        'model': 'PD705',
        'product_type': 'radio',
        'supplier': 'syndico',  #
        'stock': '200',
        'accPort': 'prop-pd705',
        'battery': 'BC2008',
        'band': 'uhf'
    }
}

## people
person_fields = [
    'name',
    'phone',  # dict of 'tel_type' : 07864654465 etc
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
    'channels'  # dict of channel info

]


def get_from_csv():
    sheets = get_data(r"C:\AmDesp\data\AmDespConfig.ods")
    clarts_dict = dict()
    attrs = sheets['CLASS_ATTRS']
    for field in attrs:
        if field:
            k = field[0]
            v = field[1:]
            clarts_dict.update({k: v})
            # (field[0], )
