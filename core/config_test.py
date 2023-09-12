from pathlib import Path

from dotenv import load_dotenv

from core.config import Config
from core.enums import ShipMode

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / 'data'
LOG_FILE = DATA_DIR / 'AmDesp.log'
CONFIG_TOML = DATA_DIR / 'user_config.toml'
# config_env = dotenv_values(DATA_DIR / ".env", verbose=True)
load_dotenv(DATA_DIR / ".env")  # take environment variables from .env.


def test_from_toml():
    for mode in ShipMode:
        for outbound in [True, False]:
            config = Config.from_toml(mode=mode, outbound=outbound)
            assert config is not None
