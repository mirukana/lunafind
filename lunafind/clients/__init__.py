# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import typing


class NoClientFoundError(Exception):
    pass


def auto_get(client: typing.Union[str, "base.Client", None]) -> "base.Client":
    if client is None:
        return net.DEFAULT

    if isinstance(client, base.Client):
        return client

    if client == "local":
        return Local()

    if isinstance(client, str):
        try:
            return net.ALIVE[client]
        except KeyError:
            pass

    raise NoClientFoundError(
        "Expected a client object, 'local', None (default net client) or the "
        "name of a client in lunafind.clients.net.ALIVE - "
        "Initialize the client object with the right name or define it in "
        "your config file."
    )


# pylint: disable=wrong-import-position
from . import base, net
from .. import config
from .danbooru import Danbooru
from .local import Local
