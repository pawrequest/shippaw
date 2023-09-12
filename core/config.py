import ctypes
import logging
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path

import PySimpleGUI as sg
from despatchbay.despatchbay_sdk import DespatchBaySDK
from despatchbay.exceptions import AuthorizationException
from dotenv import load_dotenv
from pydantic import BaseModel

from core.enums import ApiScope, Contact, DbayCreds, DefaultShippingService, HomeAddress, \
    PathsList, ShipMode, ShipmentCategory

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOG_FILE = DATA_DIR / 'AmDesp.log'
CONFIG_TOML = DATA_DIR / 'user_config.toml'
# config_env = dotenv_values(DATA_DIR / ".env", verbose=True)
load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.

...


# todo make customer work, customer name clobbers shipment name

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
    boxes: int
    send_out_date: date
    send_method: str

    outbound_id: str = None
    inbound_id: str = None


class SaleMap(ImportMap):
    shipment_name:str
    outbound_id: str = None
    inbound_id: str = None


def get_import_map(category: ShipmentCategory, mappings: dict[str, dict]) -> ImportMap:
    map_dict = mappings[category.value.lower()]
    if category == ShipmentCategory.HIRE:
        return HireMap(**map_dict)
    elif category == ShipmentCategory.SALE:
        return SaleMap(**map_dict)
    elif category == ShipmentCategory.CUSTOMER:
        return ImportMap(**map_dict)
    else:
        raise ValueError(f'Unknown ShipmentCategory {category}')


class Config_pydantic(BaseModel):
    import_map: ImportMap
    home_address: HomeAddress
    home_contact: Contact
    dbay_creds: DbayCreds
    default_shipping_service: DefaultShippingService
    paths: PathsList
    outbound: bool
    parcel_contents: str
    sandbox: bool
    return_label_email_body: str


def get_config_dict(toml_file) -> dict:
    with open(toml_file, 'rb') as g:
        return tomllib.load(g)


def get_config_pydantic(outbound, category: ShipmentCategory) -> Config_pydantic:
    config_dict = get_config_dict(toml_file=CONFIG_TOML)
    sandbox = config_dict.get('sandbox')
    dbay = config_dict.get('dbay')[scope_from_sandbox_func(sandbox=sandbox)]  # gets the names of env vars

    return Config_pydantic(
        import_map=get_import_map(category=category, mappings=config_dict['import_mappings']),
        home_address=HomeAddress(**config_dict.get('home_address')),
        home_contact=Contact(**config_dict.get('home_contact')),
        dbay_creds=DbayCreds.from_dict(api_name_user=dbay['api_user'], api_name_key=dbay['api_key']),
        default_shipping_service=DefaultShippingService(courier=dbay['courier'], service=dbay['service']),
        paths=PathsList.from_dict(paths_dict=config_dict['paths'], root_dir=ROOT_DIR),
        outbound=outbound,
        parcel_contents=config_dict.get('parcel_contents'),
        sandbox=sandbox,
        return_label_email_body=config_dict.get('return_label_email_body'),
    )


class Config:
    def __init__(self, config_dict: dict):
        self.outbound = config_dict['outbound']
        self.paths = PathsList.from_dict(paths_dict=config_dict['paths'], root_dir=ROOT_DIR)
        self.parcel_contents: str = config_dict.get('parcel_contents')
        self.sandbox: bool = config_dict.get('sandbox')
        self.import_mappings: dict = config_dict.get('import_mappings')

        self.home_address = HomeAddress(**config_dict.get('home_address'))
        self.home_contact = Contact(**config_dict.get('home_contact'))
        self.return_label_email_body = config_dict.get('return_label_email_body')

        dbay = config_dict.get('dbay')[self.scope_from_sandbox()]  # gets the names of env vars
        self.dbay_creds = DbayCreds.from_dict(api_name_user=dbay['api_user'], api_name_key=dbay['api_key'])
        self.default_shipping_service = DefaultShippingService(courier=dbay['courier'], service=dbay['service'])

    @classmethod
    def from_toml(cls, mode: ShipMode, outbound: bool):
        with open(CONFIG_TOML, 'rb') as g:
            config_dict = tomllib.load(g)
        config_dict['mode'] = mode
        config_dict['outbound'] = outbound

        return cls(config_dict=config_dict)

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

    #
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


def scope_from_sandbox_func(sandbox):
    return ApiScope.SAND.value if sandbox else ApiScope.PRODUCTION.value
