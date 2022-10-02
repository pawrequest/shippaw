from python.utils_pss.utils_pss import get_from_ods


class Config:
    def __init__(self):  # config should be above radios
        self.config_ods = r"C:\AmDesp\data\AmDespConfig.ods"
        sheet = get_from_ods(self.config_ods, 'PRODUCT_ATTRS')
        self.product = sheet.pop('PRODUCT')
        self.price_list = sheet.pop('PRICE_LIST')
PRODUCT_CNFG = Config()



class Product:
    def __init__(self):
        product_attrs = PRODUCT_CNFG.product
        for attr in product_attrs:
            setattr(self,attr,None)
        print(product_attrs)

class Radiooo(Product):
    def __init__(self, radio_dict):
        super().__init__() # pointless becuase radio dict has all the attrs... super function effectivcely provided at ods level
        for k, v in radio_dict.items():
            setattr(self, k, v)
        ...
product = Product()
# radiooo = Radiooo()

# class Radio:
#     def __init__(self, radio_dict):
#         for k, v in radio_dict.items():
#             setattr(self, k, v)


'''
class Config:
    def __init__(self):  
        self.config_ods = r"C:\AmDesp\data\AmDespConfig.ods"
        self.rads_w_bat_sers = ['hytera_pd705']

        class RadioConfig:
            def __init__(self, ods):
                radios_dict = get_from_ods(ods, 'RADIO_DICT')
                for radio, properties in radios_dict.items():
                    setattr(self, radio, properties)
                # self.radios = get_from_ods(self.config_ods, 'RADIO_DICT')
                print(f"DSGSDGSDG")

        self.radios = RadioConfig(self.config_ods)


PROG_CNFG = Config()
'''

# product classes


'''
class Product:
    def __init__(self, dict):
        for field in CONFIG_CLASS['PRODUCT']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Radio(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CONFIG_CLASS['RADIO']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Battery(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CONFIG_CLASS['BATTERY']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Charger(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CONFIG_CLASS['CHARGER']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class AUDIO_ACC(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CONFIG_CLASS['AUDIO_ACC']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")


class Price_List(Product):
    def __init__(self, dict):
        Product.__init__(self, dict)
        for field in CONFIG_CLASS['PRICES']:
            if field in dict.keys():
                setattr(self, field, dict[field])
            else:
                print(f"ERROR - input missing {field}")

#'''
