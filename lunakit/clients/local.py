# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

from pathlib import Path
from random import randint
from typing import Any, Dict, List, Optional, Union

import simplejson
from dataclasses import dataclass
from lazy_object_proxy import Proxy as LazyProxy

from . import base
from .. import filtering


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
                    continue

        posts = sorted(self.path.iterdir(), key=sort_func, reverse=True)

        yield from filtering.filter_all(info_gen(posts), tags, raw=raw)


    def artcom(self, info: base.InfoType) -> List[Dict[str, Any]]:
        return simplejson.loads(self._read_res(info, "artcom.json")) or []


    def media(self, info: base.InfoType) -> Optional[LazyProxy]:
        return LazyProxy(lambda: self._read_res(info, "media.*", binary=True))


    def notes(self, info: base.InfoType) -> List[Dict[str, Any]]:
        return simplejson.loads(self._read_res(info, "notes.json")) or []


    def count_posts(self, tags: str = "") -> int:
        return len(list(self.info_search(tags)))
