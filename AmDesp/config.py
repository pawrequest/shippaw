import os
import pathlib
import subprocess
import tomllib

import PySimpleGUI as sg

from AmDesp.despatchbay.despatchbay_sdk import DespatchBaySDK


class Config:
    """
    sets up the environment
    creates a dbay client
    """

    def __init__(self):
        # get config from toml
        self.root_dir = pathlib.Path(pathlib.Path(__file__)).parent.parent
        config_path = self.root_dir / 'config.toml'
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
        for k, v in config.items():
            setattr(self, k, v)

        self.paths = config['paths']
        cmc_dll = pathlib.Path
        self.label_path = pathlib.Path(self.root_dir / self.paths['labels'])
        self.label_path.mkdir(parents=True, exist_ok=True)
        self.home_sender_id = config['home_address']['address_id']
        self.shipment_fields = config['shipment_fields']

        # commence setup
        if not pathlib.Path(self.paths['cmc_dll']).exists():
            sg.popup_error(f"Vovin CmCLibNet is not installed in expected location {cmc_dll}")
            print(f"Vovin CmCLibNet is not installed in expected location {cmc_dll}")
            self.install_cmc()

            # dbay client setup

    def get_client(self, sandbox=True):
        # parse shipmode argument and setup API keys from .env

        if sandbox:
            print("\n \t \t*** !!! SANDBOX MODE !!! *** \n")
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

    def install_cmc(self):
        subprocess.run([str(self.paths['cmc_inst']), '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           check=True)

        # except subprocess.CalledProcessError as e:
        #     print_and_pop(f"\n\nERROR: CmcLibNet Installer Failed - logging to commence is impossible \n {e}")


