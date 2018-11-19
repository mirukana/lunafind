# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import collections
import time
from copy import copy
from pathlib import Path
from threading import Lock, Thread
from typing import List, Optional, Union

from dataclasses import dataclass, field

from . import LOG, config, order
from .clients import auto, base
from .filtering import filter_all
from .post import Post


@dataclass
class Stream(collections.Iterator):
    query:    Union[str, Path] = ""
    pages:    base.PageType    = 1
    limit:    Optional[int]    = None
    random:   bool             = False
    raw:      bool             = False
    client:   base.Client      = None
    location: bool             = False

    partial_tags:   bool = False
    filter_str:     str  = ""
    stop_if_filter: str  = ""

    unfinished:     List[Post] = field(init=False, default=None)
    posts_seen:     int        = field(init=False, default=0)
    downloaded:     int        = field(init=False, default=0)

    _info_gen: base.InfoGenType = \
        field(init=False, default=None, repr=False)

    _logged_iter_done: bool = field(init=False, default=False, repr=False)
    _applied_filters:  bool = field(init=False, default=False, repr=False)


    def __post_init__(self) -> None:
        self.client     = auto.get(self.client)
        self.unfinished = []

        if self.location or isinstance(self.query, Path):
            self._info_gen = self.client.info_location(self.query)
        else:
            self._info_gen = self.client.info_search(
                self.query, self.pages, self.limit, self.random, self.raw,
                partial_tags = True if self.partial_tags else False
            )

        auto_filter = config.CFG["GENERAL"]["auto_filter"]
        if not self.filter_str.startswith(auto_filter):
            self.filter_str = " ".join((self.filter_str, auto_filter)).strip()


    def _apply_filters(self) -> None:
        if self.filter_str:
            self._info_gen = filter_all(
                items        = self._info_gen,
                terms        = self.filter_str,
                raw          = self.raw,
                partial_tags = self.partial_tags
            )

        if self.stop_if_filter.strip():
            self._info_gen = filter_all(
                items         = self._info_gen,
                terms         = self.stop_if_filter,
                raw           = self.raw,
                stop_on_match = True,
                partial_tags  = self.partial_tags
            )


    def _on_iter_done(self, discarded: int) -> None:
        if self._logged_iter_done:
            return

        log = LOG.info if self.posts_seen else LOG.warning

        log("Found %d posts%s%s.",
            self.posts_seen,
            f", {discarded} filtered" if discarded  else "",
            f" for {self.query!r}"    if self.query else "")

        self._logged_iter_done = True


    def __next__(self) -> Post:
        # Don't do this at .__post_init__ to let .filter setup stuff before
        if not self._applied_filters:
            self._apply_filters()
            self._applied_filters = True

        while True:
            try:
                info = next(self._info_gen)
            except StopIteration as stop:
                self._on_iter_done(discarded=stop.value or 0)
                raise

            post = Post(info=info, client=self.client)

            self.posts_seen += 1
            return post


    def __iter__(self) -> "Stream":
        return self


    # pylint: disable=protected-access
    def filter(self, search: str, partial_tags: bool = False) -> "Stream":
        new              = copy(self)
        new.filter_str   = " ".join((search, new.filter_str)).strip()
        new.partial_tags = partial_tags
        return new

    def stop_if(self, search: str, partial_tags: bool = False) -> "Stream":
        new                = copy(self)
        new.stop_if_filter = " ".join((search, new.stop_if_filter)).strip()
        new.partial_tags   = partial_tags
        return new

    def order(self, by: str) -> "Album":
        from .album import Album  # ævoid circular dependency
        return Album(*order.sort(list(self), by))

    __truediv__  = lambda self, search: self.filter(search)        # /
    __floordiv__ = lambda self, search: self.filter(search, True)  # //
    __mod__      = lambda self, by:     self.order(by)             # %


    def write(self,
              base_dir:  Union[str, Path] = Path("."),
              overwrite: bool             = False,
              warn:      bool             = True) -> "Stream":

        post        = None
        running     = {}
        thread_id   = 0
        max_running = int(config.CFG["GENERAL"]["parallel_requests"])
        lock        = Lock()

        def work(post: Post, thread_id: int) -> None:
            post.write(base_dir=base_dir, overwrite=overwrite, warn=warn)
            with lock:
                self.downloaded += 1
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
