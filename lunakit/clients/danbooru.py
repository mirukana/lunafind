# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import math
import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import pybooru
from dataclasses import dataclass, field
from pybooru.exceptions import PybooruError, PybooruHTTPError
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES

from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import base, net
from .. import LOG


@dataclass
class Danbooru(net.NetClient):
    site_url:  str = "https://danbooru.donmai.us"
    name:      str = "danbooru"
    username:  str = ""
    api_key:   str = ""

    default_limit: int = field(default=20,                         repr=False)
    date_format:   str = field(default="YYYY-MM-DDTHH:mm:ss.SSSZ", repr=False)

    post_url_template: str = field(default="/posts/{id}", repr=False)

    _pybooru: pybooru.Danbooru = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        super().__post_init__()

        self._pybooru = \
            pybooru.Danbooru("", self.site_url, self.username, self.api_key)

        for scheme in ("http://", "https://"):
            # pybooru.client is a requests session
            self._pybooru.client.mount(scheme,
                                       HTTPAdapter(max_retries=net.RETRY))

        net.ALIVE[self.name] = self


    def _api(self, pybooru_method: str, *args, **kwargs):
        try:
            method = getattr(self._pybooru, pybooru_method)

            with net.MAX_PARALLEL_REQUESTS_SEMAPHORE:
                return method(*args, **kwargs)

        except PybooruHTTPError as err:
            code      = err.args[1]
            long_desc = BOORU_CODES[code][1]

            LOG.error("[%d] %s", code, long_desc)

        except (PybooruError, RequestException) as err:
            LOG.error(str(err))

        # Returning [] instead of None to not crash because of `yield from`s.
        return []


    def info_search(self,
                    tags:   str           = "",
                    pages:  base.PageType = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False) -> base.InfoGenType:

        params = {"tags": tags}

        # No need for other params if search is just an ID or MD5.
        if re.match(r"^(id|md5):[a-fA-F\d]+$", tags):
            LOG.info("Fetching post %s", tags.split(":")[1])
            yield from self._api("post_list", **params)
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

            yield from self._api("post_list", **params)


    def info_url(self, url: str) -> base.InfoGenType:
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


    def artcom(self, post_id: int) -> List[Dict[str, Any]]:
        return self._api("artist_commentary_list", post_id=post_id)


    def notes(self, post_id: int) -> List[Dict[str, Any]]:
        return self._api("note_list", post_id=post_id)


    def count_posts(self, tags: str = "") -> int:
        response = self._api("count_posts", tags)
        return response["counts"]["posts"]
