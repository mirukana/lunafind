# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import logzero
import colorama

colorama.init()

LOG = logzero.setup_logger(
    formatter = logzero.LogFormatter(
        datefmt = "%H:%M:%S",
        fmt     = ("%(color)s%(levelname)1.1s %(asctime)s | "
                   "%(message)s%(end_color)s"),
        colors  = {10: colorama.Fore.CYAN,   20: colorama.Fore.GREEN,
                   30: colorama.Fore.YELLOW, 40: colorama.Fore.RED,
                   50: colorama.Fore.MAGENTA}
    )
)

# pylint: disable=wrong-import-position

from .__about__ import __doc__
from . import config
config.reload()

from .post import Post
from .stream import Stream
from .album import Album
