# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Generator, List

from . import filtering, order
from .attridict import AttrIndexedDict
from .post import Post
from .stream import Stream


class Album(AttrIndexedDict, attr="id", sugar_map=("update", "write")):
    def __init__(self, *stream_args_posts_streams, **stream_kwargs) -> None:
        super().__init__()
        self.put(*stream_args_posts_streams, **stream_kwargs)


    def __repr__(self) -> str:
        return "%s({\n%s\n})" % (
            type(self).__name__,
            "\n".join((f"    {i!r}: {p.title!r}," for i, p in self.items()))
        )


    @property
    def list(self) -> List[Post]:
        return list(self.values())


    # pylint: disable=arguments-differ
    def put(self, *stream_args_posts_streams, **stream_kwargs) -> "Album":
        stream_args = []

        for arg in stream_args_posts_streams:
            if isinstance(arg, Post):
                super().put(arg)

            elif isinstance(arg, Stream):
                super().put(*list(arg))

            else:
                stream_args.append(arg)

        if stream_args or stream_kwargs:
            super().put(*list(Stream(*stream_args, **stream_kwargs)))

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
