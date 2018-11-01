# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

"Booru clients classes"

import abc
import math
import re
import threading
from typing import Any, Dict, Generator, Iterable, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import pendulum as pend
import pybooru
import urllib3
from dataclasses import dataclass, field
from pybooru.exceptions import PybooruError, PybooruHTTPError
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import LOG, config

QueryType         = Union[int, str]
InfoGenType       = Generator[Dict[str, Any], None, None]
InfoClientGenType = Generator[Tuple[Dict[str, Any], "Client"], None, None]

IE       = Union[int, type(Ellipsis)]
PageType = Union[IE, str, Tuple[IE, IE], Tuple[IE, IE, IE], Iterable[int]]


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


class Client(abc.ABC):
    pass


ALIVE:   Dict[str, Client] = {}
DEFAULT: Optional[Client]  = None


@dataclass
class NetClient(Client, abc.ABC):
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


@dataclass
class Danbooru(NetClient):
    site_url:  str = "https://danbooru.donmai.us"
    name:      str = "danbooru"
    username:  str = ""
    api_key:   str = ""

    default_limit: int = field(default=20,                         repr=False)
    date_format:   str = field(default="YYYY-MM-DDTHH:mm:ss.SSSZ", repr=False)
    timezone:      str = field(default="US/Eastern",               repr=False)

    post_url_template: str = field(default="/posts/{id}", repr=False)

    _pybooru: pybooru.Danbooru = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        super().__post_init__()

        self._pybooru = \
            pybooru.Danbooru("", self.site_url, self.username, self.api_key)

        for scheme in ("http://", "https://"):
            # pybooru.client is a requests session
            self._pybooru.client.mount(scheme, HTTPAdapter(max_retries=RETRY))

        ALIVE[self.name] = self


    def api(self, pybooru_method: str, *args, **kwargs):
        try:
            method = getattr(self._pybooru, pybooru_method)

            with MAX_PARALLEL_REQUESTS_SEMAPHORE:
                return method(*args, **kwargs)

        except PybooruHTTPError as err:
            code      = err.args[1]
            long_desc = BOORU_CODES[code][1]

            LOG.error("[%d] %s", code, long_desc)

        except (PybooruError, RequestException) as err:
            LOG.error(str(err))

        # Returning [] instead of None to not crash because of `yield from`s.
        return []


    @staticmethod
    def _parse_pages(pages: PageType, last_page: int) -> Iterable[int]:
        is_str = isinstance(pages, str)

        if isinstance(pages, int) or (is_str and pages.isdigit()):
            return (int(pages),)

        if pages in (..., "all"):
            return range(1, last_page + 1)

        if is_str and "-" in pages:
            pages = tuple(pages.split("-"))

        if isinstance(pages, tuple):
            begin = 1         if pages[0] in (..., "begin") else int(pages[0])
            end   = last_page if pages[1] in (..., "end")   else int(pages[1])
            step  = 1         if len(pages) < 3             else int(pages[2])
            return range(begin, end + 1, step)

        if is_str and "," in pages:
            pages = [int(p) for p in pages.split(",")]

        assert hasattr(pages, "__iter__"), "pages must be iterable"
        return pages


    def info_search(self,
                    tags:   str           = "",
                    pages:  PageType      = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False) -> InfoGenType:

        params = {"tags": tags}

        # No need for other params if search is just an ID or MD5.
        if re.match(r"^(id|md5):[a-fA-F\d]+$", tags):
            LOG.info("Fetching post %s", tags.split(":")[1])
            yield from self.api("post_list", **params)
            return

        if limit:
            params["limit"] = limit

        if random is True:
            params["random"] = "true"

        if raw is True:
            params["raw"] = "true"

        total_posts = self.count_posts(params["tags"])
        last_page   = math.ceil(total_posts / (limit or self.default_limit))

        if total_posts == 0 or last_page == 0:
            LOG.warning("No posts for search %r.", tags)
            return

        for page in self._parse_pages(pages, last_page):
            if page < 1:
                continue

            params["page"] = page

            LOG.info(
                "Fetching posts%s%s%s%s",
                " for %r"       % params["tags"] if params["tags"] else "",
                " on page %d%s" % (params["page"],
                                   f"/{last_page}" if last_page else ""),
                " [random]" if "random" in params else "",
                " [raw]"    if "raw"    in params else ""
            )

            yield from self.api("post_list", **params)


    def info_url(self, url: str) -> InfoGenType:
        try:
            pid = re.search(r"/posts/(\d+)\??.*$", url).group(1)
            yield from self.info_search(tags=f"id:{pid}")
            return
        except AttributeError:  # Not a direct post URL
            pass

        parsed = parse_qs(urlparse(url).query)

        yield from self.info_search(
            tags   = parsed.get("tags",      [""]   )[-1],
            random = parsed.get("random",    [False])[-1],
            raw    = parsed.get("raw",       [False])[-1],
            pages  = int(parsed.get("page",  [1]    )[-1]),
            limit  = int(parsed.get("limit", [self.default_limit])[-1])
        )


    def count_posts(self, tags: str = "") -> int:
        response = self.api("count_posts", tags)
        return response["counts"]["posts"]


    @staticmethod
    def get_post_rank(post: "Post") -> int:
        score = post["info"]["score"]

        if score < 1:
            return score

        post_date = pend.parse(post["info"]["created_at"])

        if post_date > pend.now().subtract(days=2):
            return -1

        return math.log(score, 3) + post_date.timestamp() / 35_000


def info_auto(query:  QueryType     = "",
              pages:  PageType      = 1,
              limit:  Optional[int] = None,
              random: bool          = False,
              raw:    bool          = False,
              prefer: Danbooru      = None) -> InfoClientGenType:

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

    for post_info in method(*args):
        yield (post_info, client)


def apply_config() -> None:
    for name, cfg in config.CFG.items():
        if name in ("DEFAULT", "GENERAL"):
            continue

        assert re.match(r"[a-z0-9_-]+", name), \
               "Config section [{name}]: can only contain a-z 0-9 _ -"

        # Will be added to ALIVE (class __init__)
        client = Danbooru(
            site_url = cfg["site_url"], name    = name,
            username = cfg["username"], api_key = cfg["api_key"]
        )

        if name == config.CFG["GENERAL"]["default_booru"]:
            global DEFAULT  # pylint: disable=global-statement
            DEFAULT = client


if config.RELOADED:
    apply_config()
    config.RELOADED = False
