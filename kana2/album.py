# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import traceback
from typing import Generator, List

from zenlog import log

from . import filtering, order
from .attridict import AttrIndexedDict
from .post import Post
from .stream import Stream


class Album(AttrIndexedDict, attr="id", sugar_map=("update", "write")):
    def __init__(self, *stream_args_posts_streams, **stream_kwargs) -> None:
        super().__init__()
        self._added: int = 0
        self.put(*stream_args_posts_streams, **stream_kwargs)


    def __repr__(self) -> str:
        return "%s({\n%s\n})" % (
            type(self).__name__,
            "\n".join((f"    {i!r}: {p.title!r}," for i, p in self.items()))
        )


    @property
    def list(self) -> List[Post]:
        return list(self.values())


    def _put_stream(self, stream: Stream) -> None:
        self._added = 0

        for post in stream:
            try:
                super().put(post)
                self._added += 1
            except StopIteration:
                raise
            except Exception:
                traceback.print_exc()
                log.error("Unexpected error, trying to recover...")


    # pylint: disable=arguments-differ
    def put(self, *stream_args_posts_streams, **stream_kwargs) -> "Album":
        stream_args = []
        self._added  = 0

        try:
            for arg in stream_args_posts_streams:
                if isinstance(arg, Post):
                    super().put(arg)
                    self._added += 1

                elif isinstance(arg, Stream):
                    self._put_stream(arg)

                else:
                    stream_args.append(arg)

            if stream_args or stream_kwargs:
                self._put_stream(Stream(*stream_args, **stream_kwargs))

        except KeyboardInterrupt:
            log.warn("Caught CTRL-C, added %d posts." % self._added)
            return self

        if self._added > 1:
            log.info("Added %d posts." % self._added)
        return self


    def filter(self, search: str) -> "Album":
        return Album(*self.filter_lazy(search))

    def filter_lazy(self, search: str) -> Generator[Post, None, None]:
        yield from filtering.search(self.list, search)

    def order(self, by: str) -> "Album":
        return Album(*order.sort(self.list, by))

    __truediv__  = lambda self, search: self.filter(search)       # /
    __floordiv__ = lambda self, search: self.filter_lazy(search)  # //
    __mod__      = lambda self, by:     self.order(by)            # %