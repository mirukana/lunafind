# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import collections
import time
from copy import copy
from threading import Thread
from typing import List, Optional

from dataclasses import dataclass, field
from zenlog import log

from . import config, filtering
from .clients import (DEFAULT, Danbooru, InfoClientGenType, PageType,
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
    prefer: Danbooru      = DEFAULT

    unfinished: List[Post]        = field(init=False, default=None)
    filtered:   str               = field(init=False, default="")
    _info_gen:  InfoClientGenType = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self.filtered   = config.CFG["GENERAL"]["auto_filter"].strip()
        self.unfinished = []
        self._info_gen  = info_auto(self.query, self.pages, self.limit,
                                    self.random, self.raw, self.prefer)


    def __next__(self) -> Post:
        while True:
            info, client = next(self._info_gen)
            post         = Post(resources=[r(info, client)
                                           for r in Resource.subclasses])
            if self.filtered.strip() and \
               not list(filtering.search([post], self.filtered)):
                continue

            return post


    def __iter__(self) -> "Stream":
        return self


    def filter(self, search: str) -> "Stream":
        # pylint: disable=protected-access
        new          = copy(self)
        new.filtered = " ".join((new.filtered, search)).strip()
        return new


    def write(self, overwrite: bool = False) -> "Stream":
        post        = None
        running     = {}
        thread_id   = 0
        max_running = int(config.CFG["GENERAL"]["parallel_requests"])

        def work(post: Post, thread_id: int) -> None:
            post.write(overwrite=overwrite)
            del running[thread_id]

        try:
            while True:
                while len(running) >= max_running:
                    time.sleep(0.1)

                post = self.unfinished.pop(0) if self.unfinished else \
                       next(self)

                thread = Thread(target=work, args=(post, thread_id))
                running[thread_id] = thread
                thread.start()
                thread_id += 1

        except KeyboardInterrupt:
            log.warn("CTRL-C caught, finishing current tasks...")
            if post:
                self.unfinished.append(post)

        return self
