from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.desp_am.core.config import get_config_dict, MODEL_CONFIG_TOML, Config, config_from_dict
from src.desp_am.core.dbay_client import get_dbay_client
from src.desp_am.core.entities import ShipmentCategory

from src.desp_am.core.config import DATA_DIR, MODEL_CONFIG_TOML
load_dotenv(DATA_DIR / ".env")
TOML_FILE = MODEL_CONFIG_TOML

@pytest.fixture()
def category():
    return ShipmentCategory.HIRE


@pytest.fixture()
def dbay_client_sandbox(config_sandbox):
    return get_dbay_client(creds=config_sandbox.dbay_creds)


@pytest.fixture()
def dbay_client_production(config_production):
    return get_dbay_client(creds=config_production.dbay_creds)


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
