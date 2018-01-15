"""Danbooru-related CLI tools."""

import logging

import pybooru

from . import info, media, query, tools, utils

__author__  = "kana, julio"
__license__ = "Private"
__version__ = "0.12"
__email__   = "ym96@protonmail.ch"
__status__  = "Prototype"

PROCESSES = 16
CLIENT    = pybooru.danbooru.Danbooru("safebooru")
"""Booru client. See :class:`~pybooru.danbooru.Danbooru`"""


logging.basicConfig(level=logging.INFO)
