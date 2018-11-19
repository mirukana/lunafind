# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import math
import re
from typing import Any, Dict, Optional, Union
from urllib.parse import parse_qs, urlparse

import pendulum as pend
from dataclasses import dataclass, field

from pydecensooru import decensor, decensor_iter
# pylint: disable=no-name-in-module
from fastnumbers import fast_int

from . import base, net
from .. import LOG


@dataclass
class Danbooru(net.NetClient):
    name:      str = "danbooru"
    site_url:  str = "https://danbooru.donmai.us"
    username:  str = ""
    api_key:   str = ""

    default_limit: int = field(default=20,  repr=False)
    max_limit:     int = field(default=200, repr=False)

    url_templates: Dict[str, str] = field(default_factory=dict, repr=False)


    def __post_init__(self) -> None:
        super().__post_init__()

        self.url_templates = {
            "post":   "/posts/{id}",
            "artcom": "/artist_commentaries.json?search[post_id]={id}",
            "info":   "/posts/{id}.json",
            "notes":  "/notes.json?search[post_id]={id}",
        }

        net.ALIVE[self.name] = self


    def _api(self, endpoint_url: str, _catch_errs: bool = True, **params
            ) -> Union[None, Any]:
        response = self.http(
            "get",
            f"{self.site_url}/{endpoint_url}",
            params = params,
            auth   = ((self.username, self.api_key)
                      if self.username and self.api_key else None)
        )

        if not _catch_errs:
            return response.json()

        try:
            return response.json()
        except AttributeError:
            return []
        except ValueError as err:
            LOG.error(str(err))
            return []


    def info_id(self, post_id: int) -> Optional[base.InfoType]:
        info = self._api(f"posts/{post_id}.json")
        return decensor(info, self.site_url) if info else None


    def info_md5(self, md5: str) -> base.InfoGenType:
        yield from decensor_iter(self._api(f"posts.json", md5=md5),
                                 self.site_url)


    def info_search(self,
                    tags:   str           = "",
                    pages:  base.PageType = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False,
                    **kwargs) -> base.InfoGenType:

        # No need for other params if search is just an ID or MD5.
        if re.match(r"^id:\d+$", tags):
            post_id = fast_int(tags.split(":")[1], raise_on_invalid=True)
            LOG.info("Fetching post %d", post_id)
            info = self.info_id(post_id)
            if info:
                yield info
            return

        if re.match(r"^md5:[a-fA-F\d]+$", tags):
            LOG.info("Fetching post with MD5 %r", tags.split(":")[1])
            yield from self.info_md5(tags.split(":")[1])
            return

        params = {"tags": tags}

        if limit:
            params["limit"] = limit
            if limit > self.max_limit:
                LOG.warning("Max limit for %s is %d, got %d.",
                            self.name, self.max_limit, limit)

        # Do not pass "random=false", Danbooru sees it as true.
        if random is True:
            params["random"] = "true"

        if raw is True:
            params["raw"] = "true"

        total_posts = self.count_posts(params["tags"])
        last_page   = math.ceil(total_posts / (limit or self.default_limit))

        if total_posts == 0 or last_page == 0:
            LOG.warning("No posts for search %r.", tags)
            return

        fails = 0
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

            try:
                yield from decensor_iter(
                    self._api("posts.json", **params, _catch_errs=False),
                    self.site_url
                )
            except AttributeError:
                fails += 1
            except ValueError as err:
                LOG.error(str(err))
                fails += 1
            else:
                fails = 0

            if fails >= 5:
                LOG.error("Giving up after 5 consecutive page fetch fails, "
                          "pagination limit probably reached.")
                return


    def info_location(self, location: str) -> base.InfoGenType:
        try:
            post_id = re.search(r"/posts/(\d+)\??.*$", location).group(1)
        except AttributeError:  # Not a direct post URL
            pass
        else:
            yield self.info_id(post_id)
            return

        parsed = parse_qs(urlparse(location).query)

        yield from self.info_search(
            tags   = parsed.get("tags",      [""]   )[-1],
            random = parsed.get("random",    [False])[-1],
            raw    = parsed.get("raw",       [False])[-1],
            pages  = fast_int(parsed.get("page",  [1]    )[-1]),
            limit  = fast_int(parsed.get("limit", [self.default_limit])[-1])
        )


    def artcom(self, info: base.InfoType) -> base.ArtcomType:
        if " commentary "         not in f" {info['tag_string_meta']} " and \
           " commentary_request " not in f" {info['tag_string_meta']} " and \
            pend.parse(info["created_at"]) > pend.yesterday():
            return []

        return self._api("artist_commentaries.json",
                         **{"search[post_id]": info["id"]})


    def media(self, info: base.InfoType) -> base.MediaType:
        if "file_ext" not in info:
            LOG.warning("No media available for post %d.", info["id"])
            return None

        url_key = "large_file_url" if info["file_ext"] == "zip" else "file_url"
        answer  = self.http("get", info[url_key], stream=True)

        try:
            return answer.iter_content(8 * 1024 ** 2)
        except AttributeError:
            return None


    def notes(self, info: base.InfoType) -> base.NotesType:
        if not bool(info["last_noted_at"]):
            return []

        return self._api("notes.json", **{"search[post_id]": info["id"]})


    def count_posts(self, tags: str = "") -> int:
        return self._api("counts/posts.json", tags=tags)["counts"]["posts"]


    def get_location(self, info: base.InfoType, resource: str = "post", **_
                    ) -> Optional[str]:
        assert resource in ("post", "artcom", "info", "media", "notes")

        if resource == "media" and "file_ext" not in info:
            LOG.warning("No decensor data found for post %d, "
                        "can't report media URL.", info["id"])
            return None

        if resource == "media" and info["file_ext"] == "zip":
            return info["large_file_url"]

        if resource == "media":
            return info["file_url"]

        return "%s%s" % (self.site_url,
                         self.url_templates[resource].format(**info))
