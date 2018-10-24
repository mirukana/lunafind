# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import collections
from typing import List, Optional

from dataclasses import dataclass, field
from zenlog import log

from . import filtering
from .clients import (DEFAULT, InfoClientGenType, NetClient, PageType,
                      QueryType, info_auto)
from .post import Post
from .resources import Resource


@dataclass
class Stream(collections.Iterator):
    query:  QueryType     = ""
    pages:  PageType      = 1
    limit:  Optional[int] = None
    random: bool          = False
    raw:    bool          = False
    prefer: NetClient     = DEFAULT
    filter: Optional[str] = None

    _info_gen: InfoClientGenType = field(init=False, default=None, repr=False)
    _unfinished_dl: List[Post]   = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self._unfinished_dl = []
        self._info_gen      = info_auto(self.query, self.pages, self.limit,
                                        self.random, self.raw, self.prefer)


    def __next__(self) -> Post:
        while True:
            info, client = next(self._info_gen)
            post         = Post(resources=[r(info, client)
                                           for r in Resource.subclasses])

            if self.filter and not list(filtering.search([post], self.filter)):
                continue

            return post


    def __iter__(self) -> "Stream":
        return self


    def write(self, overwrite: bool = False) -> "Stream":
        def write_post(post: Post) -> bool:
            try:
                post.write(overwrite=overwrite)
                return True

            except KeyboardInterrupt:
                log.warn("CTRL-C caught, stream stopped at post: %d", post.id)
                self._unfinished_dl.append(post)
                return False

        for post in self._unfinished_dl:
            if not write_post(post):
                break

            self._unfinished_dl.pop(0)

        for post in self:
            if not write_post(post):
                break

        return self
