# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

"Base network client abstract class and other net-related variables."

import abc
import threading
from typing import Dict, Optional

import urllib3
from dataclasses import dataclass, field

import requests
from requests.adapters import HTTPAdapter

from . import NoClientFoundError, base
from .. import LOG, config

# Set the maximum number of total requests/threads that can be running at once.
# When doing Album.write(), a .write() thread will launch for every Post,
# and every Post will launch a .write() thread for every resource, etc.
MAX_PARALLEL_REQUESTS_SEMAPHORE = threading.BoundedSemaphore(
    int(config.CFG["GENERAL"]["parallel_requests"])
)

RETRY = urllib3.util.Retry(
    total                      = 4,
    redirect                   = 8,
    status_forcelist           = [420, 421, 429, 500, 502, 503],
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


    def http(self, http_method: str, url: str, **request_kwargs
            ) -> Optional[requests.models.Response]:
        try:
            with MAX_PARALLEL_REQUESTS_SEMAPHORE:
                response = self._session.request(
                    http_method, url, timeout=6.5, **request_kwargs
                )
                response.raise_for_status()

        except requests.exceptions.RequestException as err:
            LOG.error(str(err))
            return None

        return response


    @abc.abstractmethod
    def info_id(self, post_id: int) -> Optional[base.InfoType]:
        return None


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
