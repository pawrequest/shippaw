from pathlib import Path

from dotenv import load_dotenv

from core.config import get_config_dict, get_dbay_client
from core.enums import ApiScope, DbayCreds

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.

CONFIG_TOML = r'E:\Dev\AmDesp\core\model_user_config.toml'


def test_config_toml(config_from_toml):
    config = config_from_toml
    assert config is not None


def test_config_toml_sandbox(config_from_toml_sandbox):
    config = config_from_toml_sandbox
    assert config is not None
    assert config.sandbox is True


def test_config_toml_prod(config_from_toml_production):
    config = config_from_toml_production
    assert config is not None
    assert config.sandbox is False


def test_get_dbay_client(config_from_toml):
    config_dict = get_config_dict(toml_file=CONFIG_TOML)
    for scope in ApiScope:
        dbay = config_dict.get('dbay')[scope.value]
        dbay_creds = DbayCreds.from_dict(**dbay.get('envars'))
        client = get_dbay_client(creds=dbay_creds)
        assert client is not None
        assert client.get_account() is not None
