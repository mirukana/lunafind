# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import abc
import math
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

import pendulum as pend
from dataclasses import dataclass, field

# pylint: disable=no-name-in-module
from fastnumbers import fast_int as fint

InfoType    = Union[Dict[str, Any], "IndexedInfo"]
InfoGenType = Generator[InfoType, None, None]

IE       = Union[int, type(Ellipsis)]
PageType = Union[IE, str, Tuple[IE, IE], Tuple[IE, IE, IE], Iterable[int]]

ArtcomType = NotesType = List[Dict[str, Any]]
MediaType  = Optional[Generator[bytes, None, None]]


@dataclass
class Client(abc.ABC):
    name: str = "client"

    date_format: str = \
        field(init=False, default="YYYY-MM-DDTHH:mm:ss.SSSZ", repr=False)


    @abc.abstractmethod
    def info_md5(self, md5: str) -> InfoGenType:
        yield {}


    @abc.abstractmethod
    def info_search(self,
                    tags:   str           = "",
                    pages:  PageType      = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False,
                    **kwargs) -> InfoGenType:
        yield {}


    @abc.abstractmethod
    def artcom(self, info: InfoType) -> ArtcomType:
        return []


    @abc.abstractmethod
    def media(self, info: InfoType) -> MediaType:
        return None


    @abc.abstractmethod
    def notes(self, info: InfoType) -> NotesType:
        return []


    @abc.abstractmethod
    def count_posts(self, tags: str = "") -> int:
        return 0


    @abc.abstractmethod
    def get_url(self, info: InfoType, resource: str, **kwargs) -> str:
        return ""


    @staticmethod
    def _parse_pages(pages: PageType, last_page: int) -> Iterable[int]:
        is_str = isinstance(pages, str)

        if isinstance(pages, int) or (is_str and pages.isdigit()):
            return (fint(pages),)

        if pages in (..., "all"):
            return range(1, last_page + 1)

        if is_str and "-" in pages:
            pages = tuple(pages.split("-"))

        if isinstance(pages, tuple):
            begin = 1         if pages[0] in (..., "begin") else fint(pages[0])
            end   = last_page if pages[1] in (..., "end")   else fint(pages[1])
            step  = 1         if len(pages) < 3             else fint(pages[2])
            return range(begin, end + 1, step)

        if is_str and "," in pages:
            pages = [fint(p) for p in pages.split(",")]

        assert hasattr(pages, "__iter__"), "pages must be iterable"
        return pages


    @staticmethod
    def get_post_rank(post: "Post") -> int:
        score = post.info["score"]

        if score < 1:
            return score

        post_date = pend.parse(post.info["created_at"])

        if post_date > pend.now().subtract(days=2):
            return -1

        return math.log(score, 3) + post_date.timestamp() / 35_000
