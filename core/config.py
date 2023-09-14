import ctypes
import logging
import subprocess
import sys
import tomllib
from pathlib import Path

import PySimpleGUI as sg
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException
from dotenv import load_dotenv
from pydantic import BaseModel

from core.enums import ApiScope, Contact, DbayCreds, DefaultCarrier, HomeAddress, \
    PathsList, ShipmentCategory

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOG_FILE = DATA_DIR / 'AmDesp.log'
MODEL_CONFIG_TOML = ROOT_DIR/ 'core' / 'model_user_config.toml'
CONFIG_TOML = DATA_DIR / 'user_config.toml'
# config_env = dotenv_values(DATA_DIR / ".env", verbose=True)
load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.


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
logger.info(f'AmDesp started, '
            f'\n{ROOT_DIR=}'
            f'\n{DATA_DIR=}'
            f'\n{LOG_FILE=}'
            f'\n{CONFIG_TOML=}'
            )


class ImportMap(BaseModel):
    address_as_str: str
    contact_name: str
    email: str
    delivery_name: str
    postcode: str
    telephone: str
    customer: str


class HireMap(ImportMap):
    shipment_name: str
    boxes: str
    send_out_date: str
    send_method: str
    outbound_id: str
    inbound_id: str


class SaleMap(ImportMap):
    shipment_name: str
    outbound_id: str
    inbound_id: str

mapper_dict = {
    ShipmentCategory.HIRE: HireMap,
    ShipmentCategory.SALE: SaleMap,
    ShipmentCategory.CUSTOMER: ImportMap
}

def get_import_map(category: ShipmentCategory, mappings: dict[str, dict]) -> ImportMap:
    map_dict = mappings[category.value.lower()]
    return mapper_dict[category](**map_dict)

def get_import_map_old(category: ShipmentCategory, mappings: dict[str, dict]) -> ImportMap:
    map_dict = mappings[category.value.lower()]
    if category == ShipmentCategory.HIRE:
        return HireMap(**map_dict)
    elif category == ShipmentCategory.SALE:
        return SaleMap(**map_dict)
    elif category == ShipmentCategory.CUSTOMER:
        return ImportMap(**map_dict)
    else:
        raise ValueError(f'Unknown ShipmentCategory {category}')


class Config(BaseModel):
    import_mappings: dict[str, dict]
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


def get_config_dict(toml_file) -> dict:
    with open(toml_file, 'rb') as g:
        return tomllib.load(g)


def get_config(toml_file=CONFIG_TOML, sandbox=None) -> Config:
    config_dict = get_config_dict(toml_file=toml_file)
    sandbox = sandbox or config_dict.get('sandbox')
    scope = scope_from_sandbox_func(sandbox=sandbox)
    dbay = config_dict.get('dbay')[scope]
    dbay_creds = DbayCreds.from_dict(**dbay.get('envars'))

    default_carrier = dbay.get('default_carrier')

    return Config(
        import_mappings=config_dict['import_mappings'],
        home_address=HomeAddress(**config_dict.get('home_address')),
        home_contact=Contact(**config_dict.get('home_contact')),
        dbay_creds=dbay_creds,
        default_carrier=DefaultCarrier(**default_carrier),
        paths=PathsList.from_dict(paths_dict=config_dict['paths'], root_dir=ROOT_DIR),
        parcel_contents=config_dict.get('parcel_contents'),
        sandbox=sandbox,
        return_label_email_body=config_dict.get('return_label_email_body'),
    )


def get_dbay_client(creds: DbayCreds):
    while True:
        try:
            client = DespatchBaySDK(api_user=creds.api_user, api_key=creds.api_key)
            dbay_account = client.get_account()
            logger.info(f'Despatchbay account retrieved: {dbay_account}')
        except AuthorizationException as e:
            logger.warning(f'Unable to retrieve DBay account for {creds.api_user} : {creds.api_key}')
            creds = creds_from_user()
            continue
        else:
            return client


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


def scope_from_sandbox_func(sandbox):
    return ApiScope.SAND.value if sandbox else ApiScope.PRODUCTION.value


def creds_from_user() -> DbayCreds:
    api_user = sg.popup_get_text(f'Enter DespatchBay API User')
    api_key = sg.popup_get_text(f'Enter DespatchBay API Key')
    creds = DbayCreds(api_user=api_user, api_key=api_key)
    return creds
