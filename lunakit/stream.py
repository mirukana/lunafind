# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import collections
import re
import time
from copy import copy
from threading import Thread
from typing import List, Optional

from dataclasses import dataclass, field

from . import LOG, config, order
from .clients import base, net
from .filtering import filter_all
from .post import Post
from .resources import Resource


@dataclass
class Stream(collections.Iterator):
    query:  str           = ""
    pages:  base.PageType = 1
    limit:  Optional[int] = None
    random: bool          = False
    raw:    bool          = False
    prefer: base.Client   = None

    unfinished:     List[Post] = field(init=False, default=None)
    filter_str:     str        = field(init=False, default="")
    stop_if_filter: str        = field(init=False, default="")
    posts_seen:     int        = field(init=False, default=0)

    _info_gen: base.InfoGenType = \
        field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self.prefer     = self.prefer or net.DEFAULT
        self.unfinished = []

        if re.match(r"https?://.+", str(self.query)):
            client         = net.client_from_url(self.query)
            self._info_gen = client.info_url(self.query)
        else:
            self._info_gen = self.prefer.info_search(
                self.query, self.pages, self.limit, self.random, self.raw
            )

        self.filter_str = config.CFG["GENERAL"]["auto_filter"].strip()

        if self.filter_str:
            self._info_gen = filter_all(
                items = self._info_gen,
                terms = self.filter_str,
                raw   = self.raw
            )

        if self.stop_if_filter.strip():
            self._info_gen = filter_all(
                items = self._info_gen,
                terms = self.stop_if_filter,
                raw   = self.raw,
                stop_on_match = True
            )


    def _on_iter_done(self, discarded: int) -> None:
        if self.posts_seen == 1 and discarded == 0:
            return

        LOG.info("Found %d total posts%s%s.",
                 self.posts_seen,
                 f", {discarded} filtered" if discarded else "",
                 f" for {self.query!r}"    if self.query    else "")


    def __next__(self) -> Post:
        while True:
            try:
                info = next(self._info_gen)
            except StopIteration as stop:
                self._on_iter_done(discarded = stop.value if stop.value else 0)
                raise

            post = Post(resources=[
                r(info, self.prefer) for r in Resource.subclasses
            ])

            self.posts_seen += 1
            return post


    def __iter__(self) -> "Stream":
        return self


    # pylint: disable=protected-access
    def filter(self, search: str) -> "Stream":
        new            = copy(self)
        new.filter_str = " ".join((new.filter_str, search)).strip()
        return new

    def stop_if(self, search: str) -> "Stream":
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
