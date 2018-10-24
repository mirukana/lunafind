# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Generator, List, Union

from . import facade, filtering, order
from .attridict import AttrIndexedDict
from .clients import DEFAULT, AutoQueryType, Client
from .post import Post


class Album(AttrIndexedDict, attr="id", sugar_map=("update", "write")):
    def __init__(self, *posts: Post) -> None:
        super().__init__()
        self.put(*posts)


    def __repr__(self) -> str:
        return "%s({\n%s\n})" % (
            type(self).__name__,
            "\n".join((f"    {i!r}: {p.title!r}," for i, p in self.items()))
        )


    @property
    def list(self) -> List[Post]:
        return list(self.values())


    # pylint: disable=arguments-differ
    def put(self, *items: Union[AutoQueryType, Post], prefer: Client = DEFAULT
           ) -> "Album":

        for item in items:
            if isinstance(item, Post):
                super().put(item)
            else:
                super().put(*facade.generator(item, prefer=prefer))

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
