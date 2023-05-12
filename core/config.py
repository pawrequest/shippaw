import ctypes
import logging
import subprocess
import sys
import tomllib

import PySimpleGUI as sg
from pathlib import Path
from dotenv import dotenv_values

from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException

from core.enums import ApiScope, Contact, DbayCreds, DefaultShippingService, HomeAddress, \
    PathsList

config_env = dotenv_values(".env")
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT_DIR / 'data/AmDesp.log'
CONFIG_TOML = ROOT_DIR / 'data/user_config.toml'


def get_amdesp_logger():
    new_logger = logging.getLogger(name='AmDesp')
    # logfile = f'{__file__.replace("py", "log")}'
    logging.basicConfig(
        level=logging.INFO,
        format='{asctime} {levelname:<8} {message}',
        style='{',
        handlers=[
            logging.FileHandler(str(LOG_FILE), mode='a'),
            logging.StreamHandler(sys.stdout)
        ])
    return new_logger


logger = get_amdesp_logger()


class Config:
    def __init__(self, config_dict: dict):
        config = config_dict
        self.mode = config['mode']
        self.outbound = 'out' in config['mode']
        self.paths = PathsList.from_dict(paths_dict=config['paths'], root_dir=ROOT_DIR)
        self.parcel_contents: str = config.get('parcel_contents')
        self.sandbox: bool = config.get('sandbox')
        self.import_mapping: dict = config.get('import_mapping')

        self.home_address = HomeAddress(**config.get('home_address'))
        self.home_contact = Contact(**config.get('home_contact'))
        self.return_label_email_body = config.get('return_label_email_body')
        self.home_sender_id = str()

        dbay = config.get('dbay')[self.scope_from_sandbox()]
        self.dbay_creds = DbayCreds.from_dict(api_name_user=dbay['api_user'], api_name_key=dbay['api_key'])
        self.default_shipping_service = DefaultShippingService(courier=dbay['courier'], service=dbay['service'])

    @classmethod
    def from_toml2(cls, mode: str):
        with open(CONFIG_TOML, 'rb') as g:
            config_dict = tomllib.load(g)
        if mode == 'fake':
            mode = config_dict.get('fake_mode')
        config_dict['mode'] = mode

        return cls(config_dict=config_dict)
    #
    # def setup_amdesp(self, sandbox: bool, client: DespatchBaySDK):
    #     # candidates = client.get_address_keys_by_postcode
    #     """
    #     check system environ variables
    #     home address details - get dbay key
    #     cmclibnet
    #
    #     """
    #     if not self.check_system_env(dbay_dict=self.dbay, sandbox=sandbox):
    #         logging.exception('Unable to set Environment variables')
    #     if not self.home_address.get('dbay_key'):
    #         postcode = self.home_address.get('postal_code')
    #         if not postcode:
    #             postcode = sg.popup_get_text('No Home Postcode - enter now')
    #         candidates = client.get_address_keys_by_postcode(postcode)
    #     #     address = address_chooser_popup(candidate_dict=candidates, client=client)
    #     # self.setup_commence()

    def creds_from_user(self) -> DbayCreds:
        scope = self.scope_from_sandbox()
        api_user = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API User')
        api_key = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API Key')
        creds = DbayCreds(api_user=api_user, api_key=api_key)
        return creds

    def log_config(self):
        [logger.info(f'CONFIG - {var} : {getattr(self, var)}') for var in vars(self)]

    def scope_from_sandbox(self):
        return ApiScope.SAND.value if self.sandbox else ApiScope.PRODUCTION.value

    def get_dbay_client(self, creds: DbayCreds):
        while True:
            try:
                client = DespatchBaySDK(api_user=creds.api_user, api_key=creds.api_key)
                dbay_account = client.get_account()
                logger.info(f'Despatchbay account retrieved: {dbay_account}')
            except AuthorizationException as e:
                logger.warning(f'Unable to retrieve DBay account for {creds.api_user} : {creds.api_key}')
                creds = self.creds_from_user()
                continue
            else:
                return client

    def setup_commence(self):
        """
        looks for CmcLibNet.dll at location specified in user_config.toml,
        if not found, install it
        """
        try:
            self.paths.cmc_dll.exists()
        except Exception as e:
            logger.exception('Vovin CmcLibNet dll not found')
            try:
                self.install_cmc_lib_net()
            except Exception as e:
                logger.exception('Vovin CmcLibNet installler not found - logging to commence is impossible')

    #
    def install_cmc_lib_net(self):
        """ install Vovin CmcLibNet from exe at location specified in user_config.toml"""
        subprocess.run([self.paths.cmc_installer, '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)


#####


def run_as_admin(cmd):
    """
    Run the given command as administrator
    """
    if ctypes.windll.shell32.IsUserAnAdmin():
        return subprocess.run(cmd, shell=True)
    else:
        return subprocess.run(
            ["powershell.exe", "-Command", f"Start-Process '{cmd[0]}' -ArgumentList '{' '.join(cmd[1:])}' -Verb RunAs"],
            shell=True)


def set_despatch_env(api_user, api_key, sandbox):
    api_user_str = 'DESPATCH_API_USER'
    if sandbox:
        api_user_str += '_SANDBOX'

    api_key_str = 'DESPATCH_API_KEY'
    if sandbox:
        api_key_str += '_SANDBOX'
    #
    # cmd1 = ["setx", api_user_str, api_user, "/M"]
    # cmd2 = ["setx", api_key_str, api_key, "/M"]

    cmd3 = [["setx", api_user_str, api_user, "/M"], ["setx", api_key_str, api_key, "/M"]]

    # result1 = run_as_admin(cmd1)
    # if result1.returncode != 0:
    #     logger.error("Error:", result1.stderr)
    # else:
    #     logger.info(f"Environment variable set: {api_user_str} : {api_user}")
    #
    # result2 = run_as_admin(cmd2)
    # if result2.returncode != 0:
    #     logger.error("Error:", result2.stderr)
    # else:
    #     logger.info(f"Environment variable set: {api_key_str} : {api_key}")

    result2 = run_as_admin(cmd3)
    if result2.returncode != 0:
        logger.error("Error:", result2.stderr)
    else:
        logger.info(f"Environment variable set: {api_key_str} : {api_key}")
