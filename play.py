from enum import Enum, auto

from core.config import Config
from core.enums import ShipMode, ShipmentCategory

script = 'C:\paul\AmDesp\scripts\cmc_updater.ps1'
in_file = r'E:\Dev\AmDesp\data\rd_test_export.dbf'
outbound = True
category = ShipmentCategory.HIRE
ship_mode = ShipMode.SHIP
config = Config.from_toml(mode=ship_mode, outbound=outbound)

import pydantic_argparse

from pydantic import BaseModel, Field

from core.enums import ShipMode


class Choices(Enum):
    A = auto()
    B = auto()
    C = auto()

class Arguments(BaseModel):
    choice: Choices = Field(description="this is a required choice")


if __name__ == '__main__':
    parser = pydantic_argparse.ArgumentParser(
        model=Arguments,
        prog="Example Program",
        description="Example Description",
        version="0.0.1",
        epilog="Example Epilog",
    )
    args = parser.parse_typed_args()
    # main(args)