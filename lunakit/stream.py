# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import collections
import time
from copy import copy
from threading import Thread
from typing import List, Optional

from dataclasses import dataclass, field

from . import LOG, config, filtering, order
from .clients import base, danbooru, net
from .post import Post
from .resources import Resource


@dataclass
class Stream(collections.Iterator):
    query:  base.QueryType     = ""
    pages:  base.PageType      = 1
    limit:  Optional[int]     = None
    random: bool              = False
    raw:    bool              = False
    prefer: danbooru.Danbooru = None

    unfinished:     List[Post] = field(init=False, default=None)
    filter_str:     str        = field(init=False, default="")
    stop_if_filter: str        = field(init=False, default="")
    filtered:       int        = field(init=False, default=0)
    posts_seen:     int        = field(init=False, default=0)

    _info_gen: base.InfoClientGenType = \
        field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self.prefer = self.prefer or net.DEFAULT

        self.filter_str = config.CFG["GENERAL"]["auto_filter"].strip()
        self.unfinished = []
        self._info_gen  = net.auto_info(self.query, self.pages, self.limit,
                                        self.random, self.raw, self.prefer)


    def _on_iter_done(self) -> None:
        if not (self.posts_seen == 1 and self.filtered == 0):
            LOG.info("%d/%d posts filtered%s.",
                     self.filtered, self.posts_seen,
                     f" for {self.query!r}" if self.query else "")


    def __next__(self) -> Post:
        while True:
            try:
                info, client = next(self._info_gen)
            except StopIteration:
                self._on_iter_done()
                raise

            post = Post(resources=[
                r(info, client) for r in Resource.subclasses
            ])

            self.posts_seen += 1

            if self.stop_if_filter.strip() and \
               list(filtering.search([post], self.stop_if_filter)):
                self._on_iter_done()
                raise StopIteration

            if self.filter_str.strip() and \
               not list(filtering.search([post], self.filter_str)):
                self.filtered += 1
                continue

            return post


    def __iter__(self) -> "Stream":
        return self


    def filter(self, search: str) -> "Stream":
        # pylint: disable=protected-access
        new            = copy(self)
        new.filter_str = " ".join((new.filter_str, search)).strip()
        return new

    def stop_if(self, search: str) -> "Stream":
        # pylint: disable=protected-access
        new                = copy(self)
        new.stop_if_filter = " ".join((new.stop_if_filter, search)).strip()
        return new

    def order(self, by: str) -> "Album":
        from .album import Album  # ævoid circular dependency
        return Album(*order.sort(list(self), by))

    __truediv__  = lambda self, search: self.filter(search)  # /
    __mod__      = lambda self, by:     self.order(by)       # %


    def write(self, overwrite: bool = False, warn: bool = True) -> "Stream":
        post        = None
        running     = {}
        thread_id   = 0
        max_running = int(config.CFG["GENERAL"]["parallel_requests"])

        def work(post: Post, thread_id: int) -> None:
            post.write(overwrite=overwrite, warn=warn)
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
            LOG.warning("CTRL-C caught, finishing current tasks...")
            if post:
                self.unfinished.append(post)

        except StopIteration:
            pass

        return self
