# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import List

from .attridict import AttrIndexedDict
from .post import Post


class Album(AttrIndexedDict, attr="id", sugar_map=("update", "write")):
    # TODO: filtering, sorting

    def __init__(self, *posts: Post) -> None:
        super().__init__()
        self.put(*posts)


    def __repr__(self) -> None:
        return f"%s(%s)" % (type(self).__name__, super().__repr__())


    @property
    def posts(self) -> List[Post]:
        return list(self.values())
