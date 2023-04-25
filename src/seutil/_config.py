from pathlib import Path
import os
import sys
import yaml
from typing import *


class Macros:
    THIS_DIR: Path = Path(os.path.dirname(os.path.realpath(__file__)))
    SYS_DIR: Path = Path(sys.prefix)
    DEFAULT_CONFIG_FILE: Path = SYS_DIR / "config" / "seutil_config.json"

    if os.getenv("HOME") is not None:
        HOME_DIR: Path = Path.home()
        CONFIG_FILE: Path = HOME_DIR / ".seutil"
    else:
        CONFIG_FILE: Path = DEFAULT_CONFIG_FILE
    # end if

def get_config(key: str,
               config_file: Path = Macros.CONFIG_FILE,
               is_use_default: bool = True) -> any:
    try:
        with open(str(config_file), "r") as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
            return configs[key]
        # end with
    except (KeyError, FileNotFoundError) as e:
        if is_use_default and config_file != Macros.DEFAULT_CONFIG_FILE:
            return get_config(key, Macros.DEFAULT_CONFIG_FILE, False)
        else:
            raise e
        # end if
    # end try
