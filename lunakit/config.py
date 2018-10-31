# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import shutil
from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from typing import Optional

from appdirs import user_config_dir
from pkg_resources import resource_filename

from . import __about__

DEFAULT_FILE = resource_filename(__about__.__name__, "data/default_config.ini")
FILE         = "%s/config.ini" % user_config_dir(__about__.__pkg_name__)
CFG          = ConfigParser(interpolation=ExtendedInterpolation())
RELOADED     = False


def reload(path: Optional[str] = None) -> None:
    path = Path(path or FILE).expanduser()

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEFAULT_FILE, path)

    CFG.read_file(open(FILE, "r"))
    global RELOADED  # pylint: disable=global-statement
    RELOADED = True
