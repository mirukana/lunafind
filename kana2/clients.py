# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"Booru clients classes"

import collections
import math
import re
from pathlib import Path
from typing import Any, Dict, Generator, Mapping, Sequence, Tuple, Union
from urllib.parse import parse_qs, urlparse

import pybooru
import urllib3
from dataclasses import dataclass, field
from pybooru.exceptions import PybooruError, PybooruHTTPError
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES
from zenlog import log

from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import io, utils

AutoQueryType = Union[int, str, Sequence, Mapping[str, Any], Path]
InfoGenType   = Generator[Dict[str, Any], None, None]


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


@dataclass
class Client:
    site_url: str = ""
    name:     str = ""
    username: str = ""
    api_key:  str = ""

    _pybooru: pybooru.Danbooru = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        assert self.site_url

        if not self.name:
            self.name = urlparse(self.site_url).netloc\
                        .replace(".donmai.us", "").replace("www.", "")

        self._pybooru: pybooru.Danbooru = \
            pybooru.Danbooru("", self.site_url, self.username, self.api_key)

        for scheme in ("http://", "https://"):
            # pybooru.client is a requests session
            self._pybooru.client.mount(scheme, HTTPAdapter(max_retries=RETRY))


    # Network requests:

    def api(self, pybooru_method: str, *args, **kwargs):
        try:
            method = getattr(self._pybooru, pybooru_method)
            return method(*args, **kwargs)

        except PybooruHTTPError as err:
            code                  = err.args[1]
            url                   = err.args[2]
            short_desc, long_desc = BOORU_CODES[code]

            log.error("%s: %s - %s - %s", code, short_desc, long_desc, url)

        except (PybooruError, RequestException) as err:
            log.error(str(err))

        # Returning [] instead of None to not crash because of `yield from`s.
        return []


    def http(self, http_method: str, url: str, **request_method_kwargs):
        try:
            result = self._pybooru.client.request(
                http_method, url, timeout=6.5, **request_method_kwargs
            )
        except RequestException as err:
            log.error(str(err))

        code                  = result.status_code
        short_desc, long_desc = BOORU_CODES[code]

        if code in BOORU_CODE_GROUPS["OK"]:
            return result

        log.error("%s: %s, %s - URL: %s",
                  code, short_desc, long_desc, result.url)

        return None


    # Get post info:

    def info_search(self,
                    tags:           str  = "",
                    pages:       Union[int, Sequence[int], type(Ellipsis)] = 1,
                    posts_per_page: int  = 200,
                    random:         bool = False,
                    raw:            bool = False) -> InfoGenType:

        params = {"tags": tags}

        # No need for other params if search is just an ID or MD5.
        if re.match(r"^(id|md5):[a-fA-F\d]+$", tags):
            yield from self.api("post_list", **params)
            return

        params["limit"] = posts_per_page

        if random is True:
            params["random"] = "true"

        if raw is True:
            params["raw"] = "true"


        if isinstance(pages, int):
            pages = (pages,)

        elif pages is ...:
            total_posts = self.count_posts(params["tags"])
            last_page   = math.ceil(total_posts / params["limit"])
            pages       = range(1, last_page)

            log.info("%d pages of %d posts to get for %r.",
                     last_page, params["limit"], params["tags"])


        for page in pages:
            if page < 1:
                continue

            params["page"] = page

            log.info("Retrieving page - %s",
                     ", ".join((f"{k}: {v!r}" for k, v in params.items())))

            yield from self.api("post_list", **params)


    def info_url(self, url: str) -> InfoGenType:
        try:
            pid = re.search(r"/posts/(\d+)\??.*$", url).group(1)
            yield from self.info_search(tags=f"id:{pid}")
            return
        except AttributeError:  # Not a direct post URL
            pass

        params = parse_qs(urlparse(url).query)
        # No limit specified in url = 20 results, not 200;
        # we want to get exactly what the user sees on his browser.
        # limit parameter is extracted as a string in a list, don't know why.
        params["limit"] = int(params.get("limit")[0]) or 20

        yield from self.info_search(
            params.get("tags", ""), params.get("page", 1), params["limit"],
            params.get("random", False), params.get("raw", False)
        )


    @staticmethod
    def info_file(path) -> InfoGenType:
        posts = io.load_file(path, json=True)

        if not isinstance(posts, list):  # i.e. one post not wrapped in a list
            posts = [posts]

        yield from posts


    def info_auto(self, *queries: AutoQueryType) -> InfoGenType:
        for query in queries:
            if isinstance(query, int):
                yield from self.info_search(tags=f"id:{query}")

            elif isinstance(query, str) and re.match(r"https?://", query):
                yield from self.info_url(query)

            elif isinstance(query, str):
                yield from self.info_search(tags=query)

            elif isinstance(query, collections.Sequence):
                yield from self.info_search(*query)

            elif isinstance(query, collections.Mapping):
                yield from self.info_search(**query)

            elif isinstance(query, Path):
                yield from self.info_file(query)

            else:
                raise ValueError(f"Invalid query type: {query}")


    def count_posts(self, tags: str = "") -> int:
        response = self.api("count_posts", tags)
        return response["counts"]["posts"]


class Danbooru(Client):
    def __init__(self, username: str = "", api_key: str = ""):
        super().__init__("https://danbooru.donmai.us", "", username, api_key)


class Safebooru(Client):
    def __init__(self, username: str = "", api_key: str = ""):
        super().__init__("https://safebooru.donmai.us", "", username, api_key)


# For use by modules when user doesn't specify his own.
# TODO: change when autofiltering will be available.
DEFAULT = Safebooru()


def info_auto(*queries: AutoQueryType, prefer: Client = DEFAULT
             ) -> Generator[Tuple[Dict[str, Any], Client], None, None]:
    for query in queries:
        client = prefer

        if isinstance(query, str) and re.match(r"https?://", query):
            parts    = urlparse(query)
            site_url = f"{parts.scheme}://{parts.netloc}"

            if site_url != client.site_url:
                client = Client(f"{parts.scheme}://{parts.netloc}")

        for post_info in client.info_auto(query):
            yield (post_info, client)
