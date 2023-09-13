from pathlib import Path

from dotenv import load_dotenv

from core.config import Config, get_config, get_config_dict, scope_from_sandbox_func, get_dbay_client
from core.enums import ShipMode, ShipmentCategory, ApiScope, DbayCreds

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOG_FILE = DATA_DIR / 'AmDesp.log'
CONFIG_TOML = DATA_DIR / 'user_config.toml'
# config_env = dotenv_values(DATA_DIR / ".env", verbose=True)
load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.

def test_from_toml():
    for category in ShipmentCategory:
        for outbound in [True, False]:
            config = get_config(outbound=outbound, category=category)
            assert config is not None

def test_get_dbay_client():
    config_dict = get_config_dict(toml_file=CONFIG_TOML)
    for scope in ApiScope:
        dbay = config_dict.get('dbay')[scope.value]  # gets the names of env vars
        creds = DbayCreds.from_dict(api_user_envar=dbay['api_user'], api_key_envar=dbay['api_key'])
        client = get_dbay_client(creds=creds)
        assert client is not None


