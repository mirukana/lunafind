"""Danbooru-related CLI tools.

Attributes:
    PROCESSES: Maximum number of processes for functions using parallelization.
    CLIENT: Booru client. See :class:`~pybooru.danbooru.Danbooru`
"""

import logging

import pybooru

__all__ = ["download", "info", "media", "query", "tools", "utils"]

__author__  = "kana, julio"
__license__ = "Private"
__version__ = "0.12"
__email__   = "ym96@protonmail.ch"
__status__  = "Prototype"

PROCESSES = 8
CLIENT    = pybooru.danbooru.Danbooru("safebooru")

logging.basicConfig(level=logging.INFO)
