import ctypes
import logging
import os
import subprocess
import sys
import tomllib

import PySimpleGUI as sg
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException

from amdesp.enums import ApiScope, Contact, DateTimeMasks, DbayCreds, DefaultShippingService, FieldsList, HomeAddress, \
    PathsList

config_env = dotenv_values(".env")
load_dotenv()
# ROOT_DIR = Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
# ROOT_DIR = Path(r'r:\paul_notes\pss\amdesp')
ROOT_DIR = Path(__file__).parent.parent
LOG_FILE = ROOT_DIR.joinpath('data', 'AmDesp.log')

...


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
logger.info(f'{config_env=}\n{ROOT_DIR=}\n{LOG_FILE=}')


class Config:
    def __init__(self, config_dict: dict):
        config = config_dict
        self.mode = config['mode']
        self.paths = PathsList.from_dict(paths_dict=config['paths'], root_dir=ROOT_DIR)
        self.parcel_contents = config.get('parcel_contents')

        self.sandbox: bool = config.get('sandbox')
        self.fake_sandbox: bool = config.get('fake_sandbox')
        self.home_sender_id = str()

        self.dbay: dict = config['dbay']
        self.dbay_creds = self.get_dbay_creds()
        self.import_mapping: dict = config.get('import_mapping')

        self.home_address = HomeAddress(**config.get('home_address'))
        self.home_contact = Contact(**config.get('home_contact'))
        self.outbound = True if 'out' in config['mode'] \
            else False if 'in' in config['mode'] \
            else sg.popup_yes_no('Are we sending from home address?') == 'Yes'
        self.return_label_email_body = config.get('return_label_email_body')

    @classmethod
    def from_toml2(cls, mode: str):
        config_path = ROOT_DIR / 'data' / 'config.toml'
        user_config = ROOT_DIR / 'data' / 'user_config.toml'
        with open(config_path, 'rb') as f:
            config_dict = tomllib.load(f)
        with open(user_config, 'rb') as g:
            user_dict= tomllib.load(g)
        config_dict.update(**user_dict)

        # config_dict['sandbox'] = sandbox
        if mode == 'fake':
            mode = config_dict.get('fake_mode')
        config_dict['mode'] = mode

        return cls(config_dict=config_dict)

    def setup_amdesp(self, sandbox: bool, client: DespatchBaySDK):
        # candidates = client.get_address_keys_by_postcode
        """
        check system environ variables
        home address details - get dbay key
        cmclibnet

        """
        if not self.check_system_env(dbay_dict=self.dbay, sandbox=sandbox):
            logging.exception('Unable to set Environment variables')
        if not self.home_address.get('dbay_key'):
            postcode = self.home_address.get('postal_code')
            if not postcode:
                postcode = sg.popup_get_text('No Home Postcode - enter now')
            candidates = client.get_address_keys_by_postcode(postcode)
        #     address = address_chooser_popup(candidate_dict=candidates, client=client)
        # self.setup_commence()

    def check_system_env(self, dbay_dict: dict, sandbox: bool):
        api_user = os.environ.get(dbay_dict.get('api_user'))
        api_key = os.environ.get(dbay_dict.get('api_key'))
        client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        first_try = True
        while True:
            try:
                dbay_account = client.get_account()
                logger.info(f'Despatchbay account retrieved: {dbay_account}')
            except AuthorizationException as e:
                logger.exception(f'Client ERROR: {e}')
                first_try = False
                api_user, api_key = self.creds_from_user()
                client = DespatchBaySDK(api_user=api_user, api_key=api_key)
                continue
            else:
                if not first_try:
                    # we have a working client after input so set successful keys in system environment
                    set_despatch_env(sandbox=sandbox, api_user=api_user, api_key=api_key)
                    sg.popup_notify('System environment variables updated, restart to take effect')

                return True

    # def creds_from_user(self) -> DbayCreds:
    #     scope = ApiScope.SAND.value if self.sandbox \
    #         else ApiScope.PRODUCTION.value
    #     api_user = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API User')
    #     api_key = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API Key')
    #     creds = DbayCreds(scope=scope, api_user=api_user, api_key=api_key)
    #     return creds

    def log_config(self):
        [logger.info(f'CONFIG - {var} : {getattr(self, var)}') for var in vars(self)]

    def get_dbay_creds(self):
        scope = ApiScope.SAND.value if self.sandbox else ApiScope.PRODUCTION.value
        dbay = self.dbay.get(scope)
        courier = dbay.get('courier')
        service = dbay.get('service')

        # get the name of the system environment variable for api user
        api_name_user = dbay.get('api_user')
        api_name_key = dbay.get('api_key')

        # overwrite with actual values from environment
        api_user = os.environ.get(api_name_user)
        api_key = os.environ.get(api_name_key)

        creds = DbayCreds(api_user=api_user, api_key=api_key, courier=courier, service_id=service, scope=scope)
        return creds

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


    def setup_dbay(self):
        creds = self.get_dbay_creds()
        return self.get_dbay_client(creds)

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


