import os
import pathlib
import subprocess
import tomllib

import platformdirs

from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK


class Config:
    def __init__(self):
        # get config from toml
        config = self.get_config_from_toml()

        self.sandbox: bool = False
        self.service_id: str = ''
        self.courier_id: str = ''
        self.log_json: pathlib.Path = pathlib.Path()
        self.cmc_logger: pathlib.Path = pathlib.Path()
        self.cmc_installer: pathlib.Path = pathlib.Path()
        self.cmc_dll: pathlib.Path = pathlib.Path()
        self.labels: pathlib.Path = pathlib.Path()

        self.labels.mkdir(parents=True, exist_ok=True)

        for path in config['paths']:
            setattr(self, path, config['root_dir'] / config['paths'][path])

        self.import_mapping = config['import_mapping']
        self.home_address = config['home_address']
        self.home_sender_id = config['home_address']['address_id']
        self.shipment_fields = config['shipment_fields']
        self.export_fields = config['export_fields']
        self.address_fields = config['address_fields']
        self.contact_fields = config['contact_fields']
        self.datetime_masks = config['datetime_masks']
        self.gui_map = config['gui_map']
        self.dbay_sand = config['dbay_sand']
        self.dbay_prod = config['dbay_prod']

    @staticmethod
    def get_config_from_toml():
        root_dir = pathlib.Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
        config_path = root_dir / 'config.toml'
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        config['root_dir'] = root_dir
        return config

    def get_dbay_client(self):
        if self.sandbox:
            print(f"\n\t\t*** !!! SANDBOX MODE !!! *** \n")
            api_user = os.getenv(self.dbay_sand['api_user'])
            api_key = os.getenv(self.dbay_sand['api_key'])
            self.courier_id = self.dbay_sand['courier']
            self.service_id = self.dbay_sand['service']
        else:
            api_user = os.getenv(self.dbay_prod['api_user'])
            api_key = os.getenv(self.dbay_prod['api_key'])
            self.courier_id = self.dbay_prod['courier']
            self.service_id = self.dbay_prod['service']

        client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        return client

    #
    def install_cmc_lib_net(self):
        """ install Vovin CmcLibNet from bundled exe"""
        subprocess.run([self.cmc_installer, '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)
