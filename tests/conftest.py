import pytest

from core.config import Config, get_config, get_import_map, MODEL_CONFIG_TOML
from shipper.shipper import establish_client

from core.config import ROOT_DIR, DATA_DIR
fixtures_dir = ROOT_DIR/ 'tests' / 'fixtures'
TOML_FILE = ROOT_DIR / 'core' / 'model_user_config.toml'

@pytest.fixture(autouse=True)
def auto_establish_client(config_from_toml):
    establish_client(dbay_creds=config_from_toml.dbay_creds)


@pytest.fixture()
def config_from_toml() -> Config:
    return get_config(toml_file=TOML_FILE)


@pytest.fixture()
def config_from_toml_sandbox() -> Config:
    return get_config(toml_file=TOML_FILE, sandbox=True)


@pytest.fixture()
def config_from_toml_production() -> Config:
    return get_config(toml_file=TOML_FILE, sandbox=False)

