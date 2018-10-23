# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Any, Dict, Optional

import arrow
from lazy_object_proxy import Proxy as LazyProxy
from zenlog import log

import whratio

from .base import JsonResource


class Info(JsonResource):
    "Everything about the post (urls, tags, metadata, etc)."

    def __post_init__(self):
        super().__post_init__()
        self.enhance()


    def get_data(self) -> Dict[str, Any]:
        # self.data will be the enhanced info dict that was passed at init.
        return self.info


    def enhance(self) -> "Info":
        new = {"is_broken": False}

        new["site"]      = self.client.name
        new["site_url"]  = self.client.site_url

        new["fetch_date"] = arrow.now().format("YYYY-MM-DDTHH:mm:ss.SSSZZ")

        try:
            new["children_num"] = len(self.info["children_ids"].split())
        except AttributeError:
            new["children_num"] = 0

        new["mpixels"] = \
            (self.info["image_width"] * self.info["image_height"]) / 1_000_000

        w_h = (self.info["image_width"], self.info["image_height"])
        new["ratio_int"]   = whratio.as_int(*w_h)
        new["ratio_float"] = whratio.as_float(*w_h)

        if "file_ext" not in self.info:
            log.warn("Broken post: %d, no media info.", self.post_id)
            new["is_broken"] = True

        elif self.info["file_ext"] != "zip":
            new["is_ugoira"] = False
            new["dl_url"]    = self.info["file_url"]
            new["dl_ext"]    = self.info["file_ext"]
            new["dl_size"]   = self.info["file_size"]

        else:
            new["is_ugoira"] = True
            new["dl_url"]    = self.info["large_file_url"]  # video URL
            new["dl_ext"]    = new["dl_url"].split(".")[-1]

            def get_ugoira_size() -> Optional[int]:
                response = self.client.http("head", new["dl_url"])

                if response:
                    return int(response.headers["content-length"])

                new["is_broken"] = True
                log.warn("Broken post: %d, cannot get size.", self.post_id)
                return None

            # Doing this non-lazily makes fetching pages of ugoiras very
            # slow due to all the requests to do.
            new["dl_size"] = LazyProxy(get_ugoira_size)

        self.info.update(new)
        return self
