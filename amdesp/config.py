import os
import pathlib
import subprocess
import tomllib

import platformdirs

from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK


class Config:
    def __init__(self):
        # get config from toml
        self.log_json = pathlib.Path()
        self.cmc_logger = pathlib.Path()
        self.service_id = None
        self.courier_id = None
        self.cmc_installer = None
        self.labels = pathlib.Path()
        self.cmc_dll = pathlib.Path()
        self.root_dir = pathlib.Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))

        config_path = self.root_dir / 'config.toml'
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)

        for path in config['paths']:
            setattr(self, path, self.root_dir / config['paths'][path])
            # setattr(self, path, pathlib.Path(self.root_dir).joinpath(config['paths'][path]))
        self.labels.mkdir(parents=True, exist_ok=True)
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

    def get_dbay_client(self, sandbox=True):
        if sandbox:
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
        subprocess.run([self.cmc_installer, '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)