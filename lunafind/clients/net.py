# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

"Base network client abstract class and other net-related variables."

import abc
import threading
from typing import Dict, Optional

import urllib3
from dataclasses import dataclass, field
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import NoClientFoundError, base
from .. import LOG, config

# Set the maximum number of total requests/threads that can be running at once.
# When doing Album.write(), a .write() thread will launch for every Post,
# and every Post will launch a .write() thread for every resource, etc.
MAX_PARALLEL_REQUESTS_SEMAPHORE = threading.BoundedSemaphore(
    int(config.CFG["GENERAL"]["parallel_requests"])
)

# Missing in Pybooru. Usually Cloudflare saying the target site is down.
BOORU_CODES[502] = (
    "Bad Gateway",
    "Invalid response from the server to the gateway."
)

BOORU_CODE_GROUPS = {
    "OK":    (200, 201, 202, 204),
    "Retry": (420, 421, 429, 500, 502, 503),
    "Fatal": (400, 401, 403, 404, 410, 422, 423, 424)
}

RETRY = urllib3.util.Retry(
    total                      = 4,
    status_forcelist           = BOORU_CODE_GROUPS["Retry"],
    backoff_factor             = 1.5,
    raise_on_redirect          = False,
    raise_on_status            = False,
    respect_retry_after_header = True
)


ALIVE:   Dict[str, "NetClient"] = {}
DEFAULT: Optional["NetClient"]  = None


# pylint: disable=abstract-method
@dataclass
class NetClient(base.Client, abc.ABC):
    name:     str = "netclient"
    site_url: str = ""

    _session: requests.Session = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self._session = requests.Session()

        for scheme in ("http://", "https://"):
            self._session.mount(scheme, HTTPAdapter(max_retries=RETRY))


    def http(self, http_method: str, url: str, **request_method_kwargs):
        try:
            with MAX_PARALLEL_REQUESTS_SEMAPHORE:
                result = self._session.request(
                    http_method, url, timeout=6.5, **request_method_kwargs
                )
        except RequestException as err:
            LOG.error(str(err))

        code      = result.status_code
        long_desc = BOORU_CODES[code][1]

        if code in BOORU_CODE_GROUPS["OK"]:
            return result

        LOG.error("[%d] %s", code, long_desc)

        return None


    @abc.abstractmethod
    def info_id(self, post_id: int) -> base.InfoType:
        return {}


    @abc.abstractmethod
    def info_url(self, url: str) -> base.InfoGenType:
        yield {}


def client_from_url(url: str) -> NetClient:
    "Return a client matching an URL if possible."
    for client in ALIVE.values():
        site = client.site_url

        if url.startswith("http://") and site.startswith("https://"):
            url = url.replace("http://", "https://")

        if url.startswith(site):
            return client

    raise NoClientFoundError(f"No client known to work with site {url!r}. ")
