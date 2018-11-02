# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import math
from pathlib import Path
from random import randint
from typing import Any, Dict, List, Optional, Union

import simplejson
from dataclasses import dataclass
from lazy_object_proxy import Proxy as LazyProxy

from . import base
from .. import LOG
from ..filtering import filter_all


@dataclass
class Local(base.Client):
    name: str              = "local"
    path: Union[Path, str] = Path(".")


    def __post_init__(self) -> None:
        self.path = Path(self.path)


    def _read_res(self,
                  info:   base.InfoType,
                  file:   str,
                  binary: bool = False) -> Union[str, bytes, None]:

        path = self.path / "{}-{}".format(info["booru"], info["id"])

        try:
            path = (path / file) if "*" not in file else next(path.glob(file))
            return path.read_text() if not binary else path.read_bytes()

        except (StopIteration, FileNotFoundError):
            return None


    def _read_json(self, info: base.InfoType, file: str) -> Optional[str]:
        return simplejson.loads(self._read_res(info, file))


    def info_booru_id(self, booru: str, post_id: int) -> base.InfoType:
        fake_info = {"booru": booru, "id": post_id}
        return self._read_json(fake_info, "info.json")


    def info_search(self,
                    tags:   str                = "",
                    pages:  base.PageType      = 1,
                    limit:  base.Optional[int] = None,
                    random: bool               = False,
                    raw:    bool               = False) -> base.InfoGenType:

        def sort_func(path):
            if random:
                return randint(1, 1_000_000)

            try:
                return int(path.name.split("-")[-1])
            except ValueError:
                return -1

        def info_gen(posts):
            for post in posts:
                try:
                    yield simplejson.loads((post / "info.json").read_text())
                except (NotADirectoryError, FileNotFoundError):
                    LOG.error("Invalid post: %r.", str(post))
                    continue

        posts = sorted(self.path.iterdir(), key=sort_func, reverse=True)

        ok_i = max_i = None

        if limit:
            last  = math.ceil(len(posts) / limit)
            ok_i  = {i
                     for p in self._parse_pages(pages, last)
                     for i in range((p - 1) * limit, (p - 1) * limit + limit)}
            max_i = sorted(ok_i)[-1]

        for i, post in enumerate(filter_all(info_gen(posts), tags, raw)):
            if max_i and i > max_i:
                break

            if ok_i and i not in ok_i:
                continue

            yield post


    def artcom(self, info: base.InfoType) -> List[Dict[str, Any]]:
        return self._read_json(info, "artcom.json") or []


    def media(self, info: base.InfoType) -> Optional[LazyProxy]:
        return LazyProxy(lambda: self._read_res(info, "media.*", binary=True))


    def notes(self, info: base.InfoType) -> List[Dict[str, Any]]:
        return self._read_json(info, "notes.json") or []


    def count_posts(self, tags: str = "") -> int:
        return len(list(self.info_search(tags)))
