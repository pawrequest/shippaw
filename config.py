####  PATHS ########
# DIR_ROOT = pathlib.Path("/Amdesp")
# DIR_DATA = pathlib.Path("/Amdesp/data/")
# pathlib.Path(DIR_DATA / "Parcelforce Labels").mkdir(parents=True, exist_ok=True)  # make the labels dirs (and parents)

## Despatch Bay




'''
## get class schema
CONFIG_CLASS = {}
CONFIG_RADIO = {}


def get_product_attrs():
    global CONFIG_CLASS
    # sheets = get_data(config)
    sheets = get_data(str(CONFIG_PATH['CONFIG_FILE']))
    # config_dict = dict()
    attrs = sheets['PRODUCT_ATTRS']
    for field in attrs:
        if field:
            k = field[0]
            v = field[1:]
            CONFIG_CLASS.update({k: v})


get_product_attrs()


def get_radios():
    global CONFIG_RADIO
    sheets = get_data(str(CONFIG_PATH['CONFIG_FILE']))
    # RADIO_DICT = dict()
    radios = sheets['RADIO_DICT']
    headers = radios[0]
    for radio in radios[1:]:
        if radio:
            k = radio[0] + radio[1]
            v = dict()
            for d, header in enumerate(headers):
                v.update({headers[d]: radio[d]})
            CONFIG_RADIO.update({k: v})


get_radios()

print()

# CONFIG_PATH = {
#     'DIR_LABEL': DIR_DATA / "Parcelforce Labels",
#     'JSONFILE': DIR_DATA / "AmShip.json",
#     'XMLFILE': DIR_DATA.joinpath('AmShip.xml'),
#     'LOGFILE': DIR_DATA.joinpath("AmLog.json"),
#     'CONFIG_FILE': DIR_DATA.joinpath("AmDespConfig.Ods"),
# }
# CONFIG_FIELD = {
#     'EXPORT_EXCLUDE_KEYS': ["addressObject", "dateObject", 'service_object', 'services', 'parcels', 'shipment_return']
#     'SHIPFIELDS': ["deliveryName", "deliveryContact", "deliveryTel", "deliveryEmail", "deliveryAddress",
#                    "deliveryPostcode", "sendOutDate", "referenceNumber"],
#     'HIREFIELDS': ['deliveryTel', 'boxes', 'deliveryCharge', 'deliveryContact', 'deliveryName', 'deliveryEmail',
#                    'deliveryAddress', 'sendOutDate', 'sendOutDate', 'deliveryPostcode', 'referenceNumber',
#                    'customer']}

# class CnfgFields:
#     def __init__(self):
#         self.export_exclude_keys = ["addressObject", "dateObject", 'service_object', 'services', 'parcels', 'shipment_return']
#         self.shipment_fields = ["deliveryName", "deliveryContact", "deliveryTel", "deliveryEmail", "deliveryAddress",
#                                 "deliveryPostcode", "sendOutDate", "referenceNumber"]
#         self.hire_fields = ['deliveryTel', 'boxes', 'deliveryCharge', 'deliveryContact', 'deliveryName',
#                             'deliveryEmail',
#                             'deliveryAddress', 'sendOutDate', 'sendOutDate', 'deliveryPostcode', 'referenceNumber',
#                             'customer']
#
# class CnfgPaths:
#     def __init__(self):
#         self.DIR_LABEL = DIR_DATA / "Parcelforce Labels",
#         self.Json_File = DIR_DATA / "AmShip.json",
#         self.xml_file = DIR_DATA.joinpath('AmShip.xml'),
#         self.log_file = DIR_DATA.joinpath("AmLog.json"),
#         self.config_file = DIR_DATA.joinpath("AmDespConfig.Ods"),
'''