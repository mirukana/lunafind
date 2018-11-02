# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import abc
import math
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple, Union

import pendulum as pend

QueryType         = Union[int, str]
InfoType          = Dict[str, Any]
InfoGenType       = Generator[InfoType, None, None]
InfoClientGenType = Generator[Tuple[InfoType, "Client"], None, None]

IE       = Union[int, type(Ellipsis)]
PageType = Union[IE, str, Tuple[IE, IE], Tuple[IE, IE, IE], Iterable[int]]


class Client(abc.ABC):
    @abc.abstractmethod
    def info_search(self,
                    tags:   str           = "",
                    pages:  PageType      = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False) -> InfoGenType:
        yield {}


    @abc.abstractmethod
    def artcom(self, post_id: int) -> List[Dict[str, Any]]:
        return []


    @abc.abstractmethod
    def notes(self, post_id: int) -> List[Dict[str, Any]]:
        return []


    @abc.abstractmethod
    def count_posts(self, tags: str = "") -> int:
        return 0


    @staticmethod
    def _parse_pages(pages: PageType, last_page: int) -> Iterable[int]:
        is_str = isinstance(pages, str)

        if isinstance(pages, int) or (is_str and pages.isdigit()):
            return (int(pages),)

        if pages in (..., "all"):
            return range(1, last_page + 1)

        if is_str and "-" in pages:
            pages = tuple(pages.split("-"))

        if isinstance(pages, tuple):
            begin = 1         if pages[0] in (..., "begin") else int(pages[0])
            end   = last_page if pages[1] in (..., "end")   else int(pages[1])
            step  = 1         if len(pages) < 3             else int(pages[2])
            return range(begin, end + 1, step)

        if is_str and "," in pages:
            pages = [int(p) for p in pages.split(",")]

        assert hasattr(pages, "__iter__"), "pages must be iterable"
        return pages


    @staticmethod
    def get_post_rank(post: "Post") -> int:
        score = post["info"]["score"]

        if score < 1:
            return score

        post_date = pend.parse(post["info"]["created_at"])

        if post_date > pend.now().subtract(days=2):
            return -1

        return math.log(score, 3) + post_date.timestamp() / 35_000
