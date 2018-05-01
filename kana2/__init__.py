"""Danbooru-related CLI tools.

Attributes:
    PROCESSES: Maximum number of processes for functions using parallelization.
    CLIENT: Booru client. See :class:`~pybooru.danbooru.Danbooru`
"""

import logging

import pybooru

__all__ = ["errors", "tools", "utils", "reqwrap", "extra",
           "query", "download",
           "info", "media", "notes", "artcom"]

__author__  = "kana, julio"
__license__ = "Private"
__version__ = "0.2.0"
__email__   = "ym96@protonmail.ch"
__status__  = "Development"

PROCESSES = 8
CLIENT    = pybooru.Danbooru("safebooru")

logging.basicConfig(level=logging.INFO)
