# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"Booru clients classes"

import collections
import math
import re
from pathlib import Path
from typing import (Any, Dict, Generator, Mapping, Optional, Sequence, Tuple,
                    Union)
from urllib.parse import parse_qs, urlparse

import pendulum as pend
import pybooru
import urllib3
from dataclasses import dataclass, field
from pybooru.exceptions import PybooruError, PybooruHTTPError
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES
from zenlog import log

from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import io

AutoQueryType = Union[int, str, Sequence, Mapping[str, Any], Path]
InfoGenType   = Generator[Dict[str, Any], None, None]
PageType      = Union[int, Sequence[int], type(Ellipsis)]


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


class Client:
    pass


@dataclass
class Danbooru:
    site_url:  str = "https://danbooru.donmai.us"
    name:      str = "danbooru"
    username:  str = ""
    api_key:   str = ""

    default_limit: int = field(default=20, repr=False)

    date_format: str = field(default="YYYY-MM-DDTHH:mm:ss.SSSZ", repr=False)
    timezone:    str = field(default="US/Eastern",               repr=False)

    creation: pend.DateTime = field(default=None, repr=False)

    _pybooru: pybooru.Danbooru = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        if not self.creation:
            self.creation = pend.datetime(2005, 5, 24, tz=self.timezone)

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
                    tags:   str           = "",
                    pages:  PageType      = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False) -> InfoGenType:

        params = {"tags": tags}

        # No need for other params if search is just an ID or MD5.
        if re.match(r"^(id|md5):[a-fA-F\d]+$", tags):
            log.info("Fetching post %s", tags.split(":")[1])
            yield from self.api("post_list", **params)
            return

        last_page = None

        if limit:
            params["limit"] = limit

        if random is True:
            params["random"] = "true"

        if raw is True:
            params["raw"] = "true"


        if isinstance(pages, int):
            pages = (pages,)

        elif pages is ...:
            total_posts = self.count_posts(params["tags"])
            last_page   = math.ceil(total_posts /
                                    params.get("limit", self.default_limit))
            pages       = range(1, last_page + 1)

            log.info("Found %d posts over %d pages%s",
                     total_posts, last_page,
                     "for %r" % params["tags"] if params["tags"] else "")


        for page in pages:
            if page < 1:
                continue

            params["page"] = page

            log.info(
                "Fetching posts%s%s%s%s",
                " for %r"       % params["tags"] if params["tags"] else "",
                " on page %d%s" % (params["page"],
                                   f"/{last_page}" if last_page else ""),
                "  [random]" if "random" in params else "",
                "  [raw]"    if "raw"    in params else ""
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


    def get_post_rank(self, post: "Post") -> int:
        score = post["info"]["score"]

        if score < 1:
            return score

        post_date = pend.parse(post["info"]["created_at"])

        if post_date > pend.now().subtract(days=2):
            return -1

        post_date = post_date.timestamp()
        creation  = self.creation.timestamp()

        return math.log(score, 3) + (post_date - creation) / 35_000


DANBOORU  = Danbooru()
SAFEBOORU = Danbooru("https://safebooru.donmai.us", "safebooru")
DEFAULT   = SAFEBOORU


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
