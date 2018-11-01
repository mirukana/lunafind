# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import re
import threading

from . import net
from .. import config
from .danbooru import Danbooru


def _wait_reload_cfg() -> None:
    while True:
        config.RELOADED.wait()

        for name, cfg in config.CFG.items():
            if name in ("DEFAULT", "GENERAL"):
                continue

            assert re.match(r"[a-z0-9_-]+", name), \
                   "Config section [{name}]: can only contain a-z 0-9 _ -"

            # Will be added to ALIVE (class __init__)
            client = Danbooru(
                site_url = cfg["site_url"], name    = name,
                username = cfg["username"], api_key = cfg["api_key"]
            )

            if name == config.CFG["GENERAL"]["default_booru"]:
                net.DEFAULT = client

        config.RELOADED.clear()


threading.Thread(target=_wait_reload_cfg, daemon=True).start()
