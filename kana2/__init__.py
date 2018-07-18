"""Danbooru CLI tools"""

import importlib
import logging as log
import signal
import sys

# Must be before other relative imports to work
from .post import Post
from .store import Store

from . import config, errors, info, io, net, post, store, utils

__author__  = "kana"
__license__ = "Private"
__version__ = "0.3.6"
__email__   = "ym96@protonmail.ch"
__status__  = "Development"

log.basicConfig(level=log.INFO)

# Must be effective ASAP, hide traceback when hitting CTRL-C (SIGINT).
try:
    signal.signal(signal.SIGINT, lambda sig_nbr, _: sys.exit(128 + sig_nbr))
except ValueError: # Happens if we're imported from a thread:
    pass
