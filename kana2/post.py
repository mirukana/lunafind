# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from .attridict import AttrIndexedDict
from .resources import Info, Resource
from .utils import join_comma_and


class Post(AttrIndexedDict, attr="title", sugar_map=("update", "write")):
    "Collection of resources belonging to a specific post."

    def __init__(self, *resources: Resource) -> None:
        super().__init__()

        passed_info = [r for r in resources if isinstance(r, (dict, Info))]

        if not passed_info:
            raise TypeError("Info object required to initialize Post.")
        elif len(passed_info) > 1:
            raise TypeError("Too many Info object passed to Post, max is 1.")

        self.put(*resources)


    @property
    def id(self) -> int:
        return self.info["id"]


    @property
    def title(self) -> str:
        kinds = {k: join_comma_and(*self.info[f"tag_string_{k}"].split())
                 for k in ("character", "copyright", "artist")}

        return "{character} ({copyright}) drawn by {artist}".format(**kinds)


    def __repr__(self) -> None:
        return f"%s(id={self.id}, title='{self.title}')" % type(self).__name__
