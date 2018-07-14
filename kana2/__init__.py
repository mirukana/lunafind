"""Danbooru CLI tools"""

import importlib
import logging as log
import signal
import sys

from .post import Post
from .store import Store

from . import config, errors, info, net, post, store, utils

__author__  = "kana"
__license__ = "Private"
__version__ = "0.3.5"
__email__   = "ym96@protonmail.ch"
__status__  = "Development"

log.basicConfig(level=log.INFO)

# Must be effective ASAP, hide traceback when hitting CTRL-C (SIGINT).
signal.signal(signal.SIGINT, lambda signal_nbr, _: sys.exit(128 + signal_nbr))
