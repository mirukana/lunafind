# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import re
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


def reload(path: Optional[str] = None) -> None:
    path = Path(path or FILE).expanduser()

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEFAULT_FILE, path)

    CFG.read_file(open(FILE, "r"))
    _reload_clients()


def _reload_clients() -> None:
    from . import clients  # Avoid circular import

    for name, cfg in CFG.items():
        if name in ("DEFAULT", "GENERAL"):
            continue

        assert re.match(r"[a-z0-9_-]+", name), \
               "Config section [{name}]: can only contain a-z 0-9 _ -"

        # Will be added to net.ALIVE (class __init__)
        client = clients.danbooru.Danbooru(
            site_url = cfg["site_url"], name    = name,
            username = cfg["username"], api_key = cfg["api_key"]
        )

        if name == CFG["GENERAL"]["default_booru"]:
            clients.net.DEFAULT = client
