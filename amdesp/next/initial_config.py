"""
take data from user_config.toml and populate config.toml
check / establish environment variables
get dbay client, confirm primary sender address + set in config
"""
import logging
import os
import tomllib
from pathlib import Path

import PySimpleGUI as sg
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException

from amdesp.config import set_despatch_env
from amdesp.config import get_amdesp_logger

logger = get_amdesp_logger()

user_config_path = r'C:\paul\AmDesp\data\user_config2.toml'
config_path = r'C:\paul\AmDesp\data\config2.toml'


def injest_user_config(user_config_path, config_path):
    with (open(config_path, 'wb') as f,
          open(user_config_path, 'rb') as g):
        config = tomllib.load(f)
        user_config = tomllib.load(g)
    return config | user_config


config = injest_user_config(user_config_path, config_path)


def setup_amdesp(self, sandbox: bool, client: DespatchBaySDK):
    # candidates = client.get_address_keys_by_postcode
    """
    check system environ variables for either sandbox or real money Dbay client
    home address details - get dbay key
    cmclibnet

    """
    if not self.check_system_env(dbay_dict=config.dbay, sandbox=sandbox):
        logging.exception('Unable to set Environment variables')
    if not self.home_address.get('dbay_key'):
        postcode = self.home_address.get('postal_code')
        if not postcode:
            postcode = sg.popup_get_text('No Home Postcode - enter now')
        candidates = client.get_address_keys_by_postcode(postcode)
        # address = address_chooser_popup(candidate_dict=candidates, client=client)
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
