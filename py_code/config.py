import tomllib

class Fields:
    def __init__(self, fields_dict:dict):
        for k,v in fields_dict.items():
            setattr(self,k,v)


with open (r'E:\Dev\AmDesp\config.toml', 'rb') as f:
    config_imported = tomllib.load(f)

an_object = Fields(config_imported)
