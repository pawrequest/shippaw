"""
take data from user_config.toml and populate config.toml
check / establish environment variables
get dbay client, confirm primary sender address + set in config
"""
import tomllib
from pathlib import Path

user_config_path =  r'C:\paul\AmDesp\data\user_config2.toml'
config_path =  r'C:\paul\AmDesp\data\config2.toml'


class Amdesp:
    ...
    def injest_user_config(self,user_config_path, config_path):
        with open(config_path, 'wb') as f:
            config = tomllib.load(f)
        with open(user_config_path, 'rb') as f:
            user_config = tomllib.load(f)
        ...

    injest_user_config(user_config_path, config_path)



