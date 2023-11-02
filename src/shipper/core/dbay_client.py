import logging
import os
from dataclasses import dataclass

import PySimpleGUI as sg
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException

logger = logging.getLogger(__name__)


class DbayClientWrapper(DespatchBaySDK):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_calls = 0

    def _log_api_call(self, method_name, *args, **kwargs):
        """ Log API call with its name and parameters """
        self.api_calls += 1
        logger.debug(f"API call number {self.api_calls}: {method_name}: {args=}, {kwargs=}")

    def __getattr__(self, name):
        if hasattr(super(), name) and callable(getattr(super(), name)):
            method = getattr(super(), name)

            def wrapper(*args, **kwargs):
                self._log_api_call(name, *args, **kwargs)
                return method(*args, **kwargs)

            return wrapper
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


@dataclass
class DbayCreds:
    api_user: str
    api_key: str

    @classmethod
    def from_envar_names(cls, api_user_envar, api_key_envar):
        """ takes names of environment variables for api_user and api_key and returns DbayCreds"""
        return cls(api_user=os.environ.get(api_user_envar),
                   api_key=os.environ.get(api_key_envar))

    @classmethod
    def from_user(cls):
        return cls(api_user=sg.popup_get_text(f'Enter DespatchBay API "User"'),
                   api_key=sg.popup_get_text(f'Enter DespatchBay API "Key"'))


def get_dbay_client(creds: DbayCreds):
    while True:
        try:
            client = DbayClientWrapper(api_user=creds.api_user, api_key=creds.api_key)
            dbay_account = client.get_account()
            logger.info(f'Despatchbay account retrieved: {dbay_account}')
        except AuthorizationException as e:
            logger.warning(f'Unable to retrieve DBay account for {creds.api_user} : {creds.api_key}')
            creds = creds_from_user()
            continue
        else:
            # client = cast(DespatchBaySDK, client)
            return client


def creds_from_user() -> DbayCreds:
    api_user = sg.popup_get_text(f'Enter DespatchBay API User')
    api_key = sg.popup_get_text(f'Enter DespatchBay API Key')
    creds = DbayCreds(api_user=api_user, api_key=api_key)
    return creds
