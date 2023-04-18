import ctypes
import functools
import json
import logging
import os
import subprocess
import sys
import tomllib
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum

import PySimpleGUI as sg
import platformdirs
from amdesp.despatchbay.despatchbay_sdk import DespatchBaySDK
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

from amdesp.despatchbay.exceptions import AuthorizationException

config_env = dotenv_values(".env")
load_dotenv()
ROOT_DIR = Path(platformdirs.user_data_dir(appname='AmDesp', appauthor='PSS'))
LOG_FILE = ROOT_DIR.joinpath('data', 'AmDesp.log')

...


class ShipMode(Enum):
    SHIP_OUT = 'ship_out'
    SHIP_IN = 'ship_in'
    TRACK_OUT = 'track_out'
    TRACK_IN = 'track_in'


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


class PathsList:
    def __init__(self, paths_dict: dict):
        self.log_json: Path = Path()
        self.cmc_logger: Path = Path()
        self.cmc_installer: Path = Path()
        self.cmc_dll: Path = Path()
        self.labels: Path = Path()
        self.user_data = Path()
        for name, path in paths_dict.items():
            setattr(self, name, ROOT_DIR / path)
        self.labels.mkdir(parents=True, exist_ok=True)


class FieldsList:
    def __init__(self, fields_list_dict: dict):
        self.address = [str()]
        self.contact = [str()]
        self.export = [str()]
        self.shipment = [str()]
        for field_type, fields in vars(self).items():
            if not field_type in fields_list_dict.keys():
                field_type = sg.popup_get_text(
                    f'{field_type.title()} Field list not found, please enter a comma separated list')
            setattr(self, field_type, fields_list_dict.get(field_type))


class Config:
    def __init__(self, config_dict: dict):
        config = config_dict
        self.mode = config['mode']
        self.service_id: str = ''
        self.courier_id: str = ''
        self.paths = PathsList(config['paths'])
        self.fields = FieldsList(config['fields'])

        self.sandbox: bool = config.get('sandbox')
        self.home_sender_id = str()

        self.datetime_masks: dict = config.get('datetime_masks')
        self.dbay: dict = config.get('dbay')
        self.import_mapping: dict = config.get('import_mapping')
        self.gui_map: dict = config.get('gui_map')

        self.home_address: dict = config.get('home_address')
        self.home_contact = Contact(**config.get('home_contact'))
        self.outbound = True if 'out' in config['mode'] else False

    @classmethod
    def from_toml2(cls, sandbox: bool, mode: str):
        config_path = ROOT_DIR / 'data' / 'config.toml'
        user_config = ROOT_DIR / 'data' / 'user_config.toml'
        with open(config_path, 'rb') as f:
            config_dict = tomllib.load(f)
        with open(user_config, 'rb') as g:
            user_dict= tomllib.load(g)
        config_dict.update(**user_dict)

        config_dict['sandbox'] = sandbox
        config_dict['mode'] = mode
        logger.info(f'FROM TOML - {[(k, v) for k, v in os.environ.items() if "despatch" in k.lower()]}')

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
                api_user, api_key = self.creds_from_user(sandbox=sandbox)
                client = DespatchBaySDK(api_user=api_user, api_key=api_key)
                continue
            else:
                if not first_try:
                    # we have a working client after input so set successful keys in system environment
                    set_despatch_env(sandbox=sandbox, api_user=api_user, api_key=api_key)
                    sg.popup_notify('System environment variables updated, restart to take effect')

                return True

    def creds_from_user(self, sandbox) -> tuple:
        scope = 'sand' if sandbox else 'prod'
        api_user = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API User')
        api_key = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API Key')
        return api_user, api_key

    def log_config(self):
        [logger.info(f'CONFIG - {var} : {getattr(self, var)}') for var in vars(self)]

    def get_dbay_client_ag(self, sandbox: bool):
        scope = 'sand' if sandbox else 'prod'
        dbay_dict = self.dbay[scope]
        self.dbay = dbay_dict

        # get the name of the system environment variable for api user
        api_user = dbay_dict.get('api_user')
        api_key = dbay_dict.get('api_key')

        # overwrite with values from environment
        api_user = os.environ.get(api_user)
        api_key = os.environ.get(api_key)

        # get a client, which may be bunk so attempt to use it, if fail, get new api creds from user and try again.
        # if succed at second or later attempt, write successful values to system environment for future reference
        client = DespatchBaySDK(api_user=api_user, api_key=api_key)
        logger.info(f'GETTING DESPATCH CLIENT, API KEYS= {api_user} : {api_key}')
        first_try = True
        while True:
            try:
                dbay_account = client.get_account()
                logger.info(f'Despatchbay account retrieved: {dbay_account}')
            except AuthorizationException as e:
                first_try = False
                api_user, api_key = self.creds_from_user(sandbox=sandbox)
                client = DespatchBaySDK(api_user=api_user, api_key=api_key)
                continue
            else:
                if not first_try:
                    # we have a working client after input so set successful keys in system environment
                    set_despatch_env(sandbox=sandbox, api_user=api_user, api_key=api_key)
                    sg.popup_notify('System environment variables updated, restart to take effect')

                return client

    def setup_commence(self):
        """ looks for CmcLibNet in prog files, if absent attempts to install exe located at path defined in config.toml"""
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
        """ install Vovin CmcLibNet from bundled exe"""
        subprocess.run([self.paths.cmc_installer, '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

#####


def run_as_admin(cmd):
    """
    Run the given command as administrator
    """
    # Elevate the current process to admin
    if ctypes.windll.shell32.IsUserAnAdmin():
        return subprocess.run(cmd, shell=True)

    # Spawn a new process with admin privileges
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

    cmd1 = ["setx", api_user_str, api_user, "/M"]
    cmd2 = ["setx", api_key_str, api_key, "/M"]

    result1 = run_as_admin(cmd1)
    if result1.returncode != 0:
        logger.error("Error:", result1.stderr)
    else:
        logger.info(f"Environment variable set: {api_user_str} : {api_user}")

    result2 = run_as_admin(cmd2)
    if result2.returncode != 0:
        logger.error("Error:", result2.stderr)
    else:
        logger.info(f"Environment variable set: {api_key_str} : {api_key}")


BestMatch = namedtuple('BestMatch', ['str_matched', 'address', 'category', 'score'])
Contact = namedtuple('Contact', ['email', 'telephone', 'name'])
