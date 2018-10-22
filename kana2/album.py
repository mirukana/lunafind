# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Dict, Generator, List, Tuple

from . import filtering
from .attridict import AttrIndexedDict
from .post import Post


class Album(AttrIndexedDict, attr="id", sugar_map=("update", "write")):
    def __init__(self, *posts: Post) -> None:
        super().__init__()
        self.put(*posts)


    def __repr__(self) -> None:
        return f"%s(%s)" % (type(self).__name__, super().__repr__())


    @property
    def posts(self) -> List[Post]:
        return list(self.values())


    def find(self, search: str) -> "Album":
        return Album(*self.find_lazy(search))


    def find_lazy(self, search: str) -> Generator[Post, None, None]:
        yield from filtering.search(self.posts, search)


    def find_analyze(self, search: str
                    ) -> Generator[Tuple[Post, Dict[str, bool]], None, None]:
        yield from filtering.search(self.posts, search, yield_analyze=True)
