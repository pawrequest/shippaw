from pathlib import Path

import pytest
from despatchbay.despatchbay_sdk import DespatchBaySDK
from dotenv import load_dotenv

from core.config import Config, MODEL_CONFIG_TOML, config_from_dict, get_config_dict
from core.dbay_client import get_dbay_client
from core.enums import ShipmentCategory

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
load_dotenv(DATA_DIR / ".env")
TOML_FILE = ROOT_DIR / 'core' / 'model_user_config.toml'


@pytest.fixture(params=list(ShipmentCategory))
def category(request):
    return request.param
#
# @pytest.fixture()
# def category():
#     return ShipmentCategory.HIRE


@pytest.fixture()
def config_dict_from_toml():
    return get_config_dict(toml_file=MODEL_CONFIG_TOML)


@pytest.fixture()
def config_sandbox(config_dict_from_toml) -> Config:
    return config_from_dict(config_dict=config_dict_from_toml, sandbox=True)


def test_config_sandbox(config_sandbox):
    assert isinstance(config_sandbox, Config)
    assert config_sandbox.sandbox is True


@pytest.fixture()
def config_production(config_dict_from_toml) -> Config:
    return config_from_dict(config_dict=config_dict_from_toml, sandbox=False)


def test_config_prod(config_production):
    assert isinstance(config_production, Config)
    assert config_production.sandbox is False


@pytest.fixture()
def dbay_client_sandbox(config_sandbox):
    return get_dbay_client(creds=config_sandbox.dbay_creds)


# def test_client_sandbox(dbay_client_sandbox):
#     assert isinstance(dbay_client_sandbox, DespatchBaySDK)
#     balance = dbay_client_sandbox.get_account_balance().balance
#     assert balance == 1000.0
#

@pytest.fixture()
def dbay_client_production(config_production):
    return get_dbay_client(creds=config_production.dbay_creds)

#
# def test_client_production(dbay_client_production):
#     assert isinstance(dbay_client_production, DespatchBaySDK)
#     balance = dbay_client_production.get_account_balance().balance
#     assert isinstance(balance, float)
