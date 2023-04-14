import functools
import logging
import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass

import platformdirs

from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from pathlib import Path

ROOT_DIR = Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
LOG_FILE = ROOT_DIR.joinpath('data', 'AmDesp.log')
...



def get_amdesp_logger():
    logger = logging.getLogger(name='AmDesp_logger')
    # logfile = f'{__file__.replace("py", "log")}'
    logging.basicConfig(
        level=logging.INFO,
        format='{asctime} {levelname:<8} {message}',
        style='{',
        handlers=[
            logging.FileHandler(str(LOG_FILE), mode='a'),
            logging.StreamHandler(sys.stdout)
        ])
    return logger

logger = get_amdesp_logger()

@dataclass
class Config:
    def __init__(self, config_dict: dict):
        # get config from toml
        config = config_dict
        self.service_id: str = ''
        self.courier_id: str = ''
        self.log_json: Path = Path()
        self.cmc_logger: Path = Path()
        self.cmc_installer: Path = Path()
        self.cmc_dll: Path = Path()
        self.labels: Path = Path()
        self.amdesp_log: Path = Path()

        self.labels.mkdir(parents=True, exist_ok=True)

        for path in config['paths']:
            setattr(self, path, ROOT_DIR / config['paths'][path])

        self.sandbox: bool = config['sandbox']
        self.home_sender_id: str = config['home_address']['address_id']
        self.shipment_fields: list = config['shipment_fields']
        self.export_fields: list = config['export_fields']
        self.address_fields: list = config['address_fields']
        self.contact_fields: list = config['contact_fields']

        self.datetime_masks: dict = config['datetime_masks']
        self.home_address: dict = config['home_address']
        self.dbay: dict = config['dbay']
        self.import_mapping: dict = config['import_mapping']
        self.gui_map = config['gui_map']
        # self.logger = get_amdesp_logger()
        ...

    @classmethod
    def from_toml2(cls, sandbox: bool):
        config_path = ROOT_DIR / 'config.toml'
        with open(config_path, 'rb') as f:
            config_dict = tomllib.load(f)
        config_dict['dbay'] = config_dict['dbay']['sand'] if sandbox else config_dict['dbay']['prod']
        config_dict['sandbox'] = sandbox
        return cls(config_dict=config_dict)

    # @staticmethod
    # def dict_from_toml():
    #
    #     config_path = ROOT_DIR / 'config.toml'
    #     with open(config_path, 'rb') as f:
    #         config = tomllib.load(f)
    #     config['root_dir'] = ROOT_DIR
    #     return config

    def log_config(self):
        [logger.info(f'CONFIG - {var} : {getattr(self, var)}') for var in vars(self)]

    def get_dbay_client_ag(self, dbay_dict: dict):
        api_user = os.getenv(dbay_dict['api_user'])
        api_key = os.getenv(dbay_dict['api_key'])
        client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        return client

    def setup_commence(self):
        """ looks for CmcLibNet in prog files, if absent attempts to install exe located at path defined in config.toml"""
        try:
            self.cmc_dll.exists()
        except Exception as e:
            logging.warning('Vovin cmc_lib_net is not installed')
            try:
                self.install_cmc_lib_net()
            except Exception as e:
                logging.error("Unable to find or install CmcLibNet - logging to commence is impossible"
                              f"\n{e}")
                # error message built into cmclibnet installer

    #
    def install_cmc_lib_net(self):
        """ install Vovin CmcLibNet from bundled exe"""
        subprocess.run([self.cmc_installer, '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

    #####


# #
# #
# # @dataclass
# # class Config:
# #     sandbox: bool
# #
# #     root_dir: Path
# #
# #     # service_id: str
# #     # courier_id: str
# #
# #     shipment_fields: list
# #     export_fields: list
# #     address_fields: list
# #     contact_fields: list
# #
# #     import_mapping: dict
# #     home_address: dict
# #     datetime_masks: dict
# #     gui_map: dict
# #     dbay: dict
# #     paths: dict[str:Path]
#
#     @classmethod
#     def from_toml(cls, sandbox: bool, root_dir: Path):
#         config_path = root_dir / 'config.toml'
#         with open(config_path, 'rb') as f:
#             config = tomllib.load(f)
#         config['root_dir'] = root_dir
#         config['sandbox'] = sandbox
#         config['dbay'] = config['dbay']['sand'] if sandbox else config['dbay']['prod']
#         return cls(**config)

def log_function(logger):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for object_name, object in kwargs.items():
                if isinstance(object, str):
                    logging.info(f'{func.__name__.upper()} - {object_name} - {object}')

                else:
                    for var in vars(object):
                        logging.info(f'{func.__name__.upper()} - {object_name} - {var} - {getattr(object, var)}')

            result = func(*args, **kwargs)
            logging.info(f'Finished calling function {func.__name__}')
            return result

        return wrapper

    return decorator
#
# @dataclass
# class ConfigOld:
#     def __init__(self, config_dict: dict):
#         # get config from toml
#         super.__init__()
#         config = config_dict
#         self.sandbox: bool = False
#         self.service_id: str = ''
#         self.courier_id: str = ''
#         self.log_json: Path = Path()
#         self.cmc_logger: Path = Path()
#         self.cmc_installer: Path = Path()
#         self.cmc_dll: Path = Path()
#         self.labels: Path = Path()
#
#         self.labels.mkdir(parents=True, exist_ok=True)
#
#         for path in config['paths']:
#             setattr(self, path, config['root_dir'] / config['paths'][path])
#
#         self.import_mapping = config['import_mapping']
#         self.home_address = config['home_address']
#         self.home_sender_id = config['home_address']['address_id']
#         self.shipment_fields = config['shipment_fields']
#         self.export_fields = config['export_fields']
#         self.address_fields = config['address_fields']
#         self.contact_fields = config['contact_fields']
#         self.datetime_masks = config['datetime_masks']
#         self.gui_map = config['gui_map']
#         self.dbay_sand = config['dbay_sand']
#         self.dbay_prod = config['dbay_prod']
#
#
#
#
#     @staticmethod
#     def config_dict_from_toml():
#         root_dir = Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
#         config_path = root_dir / 'config.toml'
#         with open(config_path, 'rb') as f:
#             config = tomllib.load(f)
#         config['root_dir'] = root_dir
#         return config
#
#     #####
