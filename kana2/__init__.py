"""Danbooru-related CLI tools.

Attributes:
    CLIENT: Booru client. See :class:`~pybooru.danbooru.Danbooru`
"""

import logging
import signal
import sys

import pybooru

__all__ = ["post", "info", "net", "errors", "utils"]

__author__  = "kana"
__license__ = "Private"
__version__ = "0.3.0"
__email__   = "ym96@protonmail.ch"
__status__  = "Development"

CLIENT = pybooru.Danbooru("safebooru")

logging.basicConfig(level=logging.INFO)

# Must be effective ASAP, hide traceback when hitting CTRL-C (SIGINT).
signal.signal(signal.SIGINT, lambda signal_nbr, _: sys.exit(128 + signal_nbr))
