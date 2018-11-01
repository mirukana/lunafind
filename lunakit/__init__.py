# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import logzero
import blessed

TERM = blessed.Terminal()

LOG = logzero.setup_logger(
    formatter = logzero.LogFormatter(
        datefmt = "%H:%M:%S",
        fmt     = ("%(color)s%(levelname)1.1s %(asctime)s | "
                   "%(message)s%(end_color)s"),
        colors  = {10: TERM.cyan, 20: TERM.green, 30: TERM.yellow,
                   40: TERM.red, 50: TERM.magenta}
    )
)

# pylint: disable=wrong-import-position

from .__about__ import __doc__
from . import config
config.reload()

from .post import Post
from .stream import Stream
from .album import Album
