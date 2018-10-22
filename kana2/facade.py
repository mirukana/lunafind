# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Optional

from zenlog import log

from .albums import Album
from .clients import DEFAULT, AutoQueryType, Client, InfoGenType, info_auto
from .post import Post
from .resources import Artcom, Info, Media, Notes


def one(query: AutoQueryType = "", client: Client = DEFAULT) -> Optional[Post]:
    try:
        info = Info(next(client.info_auto(query)), client)
    except StopIteration:
        log.warn("No post found for query %r.", query)
        return None

    return Post(info, Artcom(info), Media(info), Notes(info))


def generator(*queries: AutoQueryType, prefer: Client = DEFAULT
             ) -> InfoGenType:

    if not queries:
        queries = ("",)  # latest posts/home page on booru

    for query in queries:
        found = 0

        for info_dict, client in info_auto(query, prefer=prefer):
            found += 1

            info = Info(info_dict, client)
            yield Post(info, Artcom(info), Media(info), Notes(info))

        if not found:
            log.warn("No post found for query %r.", query)


def album(*queries: AutoQueryType, prefer: Client = DEFAULT) -> Album:
    return Album(*generator(*queries, prefer=prefer))
