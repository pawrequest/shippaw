import logging
import subprocess
import sys
import tomllib
from pathlib import Path

import PySimpleGUI as sg
from dotenv import load_dotenv
from pydantic import BaseModel

from .dbay_client import DbayCreds
from .entities import Contact, DefaultCarrier, HomeAddress, \
    PathsList

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOG_FILE = DATA_DIR / 'AmDesp.log'
CONFIG_TOML = DATA_DIR / 'config.toml'

load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.

logger = logging.getLogger(name=__name__)




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


class Config(BaseModel):
    # import_mappings: dict[str, dict]
    home_address: HomeAddress
    home_contact: Contact
    dbay_creds: DbayCreds
    default_carrier: DefaultCarrier
    paths: PathsList
    sandbox: bool


def get_config_dict(toml_file) -> dict:
    with open(toml_file, 'rb') as g:
        return tomllib.load(g)


def config_from_dict(config_dict, sandbox=None) -> Config:
    sandbox = sandbox or config_dict.get('sandbox')
    scope = 'sandbox' if sandbox else 'production'

    dbay = config_dict.get('dbay')[scope]

    return Config(
        home_address=HomeAddress(**config_dict.get('home_address')),
        home_contact=Contact(**config_dict.get('home_contact')),
        dbay_creds=DbayCreds.from_envar_names(**dbay.get('envars')),
        default_carrier=DefaultCarrier(**dbay.get('default_carrier')),
        paths=PathsList.from_dict(paths_dict=config_dict['paths'], root_dir=ROOT_DIR),
        sandbox=sandbox,
    )
