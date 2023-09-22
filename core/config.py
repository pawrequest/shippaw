import logging
import subprocess
import sys
import tomllib
from pathlib import Path

import PySimpleGUI as sg
from dotenv import load_dotenv
from pydantic import BaseModel

from core.dbay_client import DbayCreds
from core.entities import Contact, DefaultCarrier, HomeAddress, \
    PathsList, ShipmentCategory

from core.entities import ImportMap, mapper_dict
from core.funcs import scope_from_sandbox_func

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOG_FILE = DATA_DIR / 'AmDesp.log'
MODEL_CONFIG_TOML = ROOT_DIR / 'core' / 'model_user_config.toml'
CONFIG_TOML = DATA_DIR / 'user_config.toml'

load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.

logger = logging.getLogger(name=__name__)


class Config(BaseModel):
    # import_mappings: dict[str, dict]
    import_mappings: dict[str, ImportMap]
    home_address: HomeAddress
    home_contact: Contact
    dbay_creds: DbayCreds
    default_carrier: DefaultCarrier
    paths: PathsList
    parcel_contents: str
    return_label_email_body: str
    sandbox: bool

    def creds_from_user(self) -> DbayCreds:
        scope = self.scope_from_sandbox()
        api_user = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API User')
        api_key = sg.popup_get_text(f'Enter DespatchBay {scope.title()} API Key')
        creds = DbayCreds(api_user=api_user, api_key=api_key)
        return creds

    def install_cmc_lib_net(self):
        """ install Vovin CmcLibNet from exe at location specified in user_config.toml"""
        subprocess.run([self.paths.cmc_installer, '/SILENT'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

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


def configure_logging(log_file):
    formatter = logging.Formatter('{levelname:<8} {asctime} | {name}:{lineno} | {message}', style='{')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


def get_import_mappings(mappings: dict[str, dict]) -> dict[str, ImportMap]:
    return {category.name.lower(): mapper_dict[category](**mappings[category.value.lower()])
            for category in ShipmentCategory}


def get_config_dict(toml_file) -> dict:
    with open(toml_file, 'rb') as g:
        return tomllib.load(g)


def config_from_dict(config_dict, sandbox=None) -> Config:
    sandbox = sandbox or config_dict.get('sandbox')
    scope = scope_from_sandbox_func(sandbox=sandbox)
    dbay = config_dict.get('dbay')[scope]
    mappings_dict = config_dict['import_mappings']

    return Config(
        import_mappings=get_import_mappings(mappings=mappings_dict),
        home_address=HomeAddress(**config_dict.get('home_address')),
        home_contact=Contact(**config_dict.get('home_contact')),
        dbay_creds=DbayCreds.from_envar_names(**dbay.get('envars')),
        default_carrier=DefaultCarrier(**dbay.get('default_carrier')),
        paths=PathsList.from_dict(paths_dict=config_dict['paths'], root_dir=ROOT_DIR),
        parcel_contents=config_dict.get('parcel_contents'),
        sandbox=sandbox,
        return_label_email_body=config_dict.get('return_label_email_body'),
    )


