# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Generator, List, Union

from . import facade, filtering
from .attridict import AttrIndexedDict
from .clients import DEFAULT, AutoQueryType, Client
from .post import Post


class Album(AttrIndexedDict, attr="id", sugar_map=("update", "write")):
    def __init__(self, *posts: Post) -> None:
        super().__init__()
        self.put(*posts)


    def __repr__(self) -> None:
        return f"%s(%s)" % (type(self).__name__, super().__repr__())


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


    def find(self, search: str) -> "Album":
        return Album(*self.find_lazy(search))

    def find_lazy(self, search: str) -> Generator[Post, None, None]:
        yield from filtering.search(self.list, search)

    __truediv__  = lambda self, search: self.find(search)
    __floordiv__ = lambda self, search: self.find_lazy(search)
