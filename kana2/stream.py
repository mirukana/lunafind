# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import collections
from typing import Optional

from dataclasses import dataclass, field

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


    def __post_init__(self) -> None:
        self._info_gen = info_auto(self.query, self.pages, self.limit,
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
