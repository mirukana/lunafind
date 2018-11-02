# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

"Base network client abstract class and other net-related variables."

import abc
import re
import threading
from typing import Dict, Optional

import urllib3
from dataclasses import dataclass, field
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import base
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


ALIVE:   Dict[str, base.Client] = {}
DEFAULT: Optional[base.Client]  = None


# pylint: disable=abstract-method
@dataclass
class NetClient(base.Client, abc.ABC):
    name: str = "netclient"

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


def auto_info(query:  base.QueryType = "",
              pages:  base.PageType  = 1,
              limit:  Optional[int]  = None,
              random: bool           = False,
              raw:    bool           = False,
              prefer: NetClient      = None) -> base.InfoClientGenType:
    "Return post info using the most appropriate client for search/URL/ID."

    client = prefer or DEFAULT
    method = client.info_search
    args   = (query, pages, limit, random, raw)

    if isinstance(query, int):
        args = (f"id:{query}",)

    elif isinstance(query, str) and re.match(r"https?://", query):
        for cli in ALIVE.values():
            try:
                site = cli.site_url
            except AttributeError:
                continue

            if query.startswith("http://") and site.startswith("https://"):
                query = re.sub("^http://", "https://", query)

            if query.startswith(site):
                client = cli
                break
        else:
            raise RuntimeError(f"No client to work with site {query!r}.")

        method = client.info_url
        args   = (query,)

    for post_info_ in method(*args):
        yield (post_info_, client)
