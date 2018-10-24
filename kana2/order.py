# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import random
from typing import List, Sequence

import arrow

from .post import Post

ORDER_NUM = {
    "id":       ("asc",  "id"),
    "score":    ("desc", "score"),
    "favcount": ("desc", "fav_count"),
    "mpixels":  ("desc", "mpixels"),
    "filesize": ("desc", "file_size"),
    "tagcount": ("desc", "tag_count"),  # TODO: document on dan wiki
    "gentags":  ("desc", "tag_count_general"),
    "arttags":  ("desc", "tag_count_artist"),
    "chartags": ("desc", "tag_count_character"),
    "copytags": ("desc", "tag_count_copyright"),
    "metatags": ("desc", "tag_count_meta"),

    # Non-standard:
    "dlsize": ("desc", "dl_size"),
    "width":  ("desc", "image_width"),
    "height": ("desc", "image_height"),
}

ORDER_DATE = {
    "change":         ("desc", "updated_at"),
    "comment":        ("desc", "last_commented_at"),
    "comm":           ("desc", "last_commented_at"),
    "comment_bumped": ("desc", "last_commented_bumped_at"),
    "note":           ("desc", "last_noted_at"),
    "fetched":        ("desc", "fetched_at"),  # non-standard
}

ORDER_FUNCS = {
    "rank":
        # pylint: disable=unnecessary-lambda
        lambda p: p["info"].client.get_post_rank(p),
    "random":
        lambda _: random.randint(1, 1_000_000),
    "landscape":
        lambda p: int(p["info"]["image_width"] > p["info"]["image_height"]),
    "portrait":
        lambda p: int(p["info"]["image_height"] > p["info"]["image_width"]),
}


def sort(posts: Sequence[Post], by: str) -> List[Post]:
    by_val  = by.replace("asc_", "").replace("desc_", "")

    in_dict = (ORDER_NUM   if by_val in ORDER_NUM   else
               ORDER_DATE  if by_val in ORDER_DATE  else
               ORDER_FUNCS if by_val in ORDER_FUNCS else None)

    if not in_dict:
        raise ValueError(
            f"Got {by_val!r} as ordering method, must be one of: %s" %
            ", ".join(set(ORDER_NUM) | set(ORDER_DATE) | set(ORDER_FUNCS))
        )

    if in_dict == ORDER_FUNCS:
        return sorted(posts, key=ORDER_FUNCS[by], reverse=True)

    by_full = by if by.startswith("asc_") or by.startswith("desc_") else \
              f"%s_{by}" % in_dict[by][0]

    def sort_key(post: Post) -> int:
        key = post["info"][in_dict[by_val][1]]
        return arrow.get(key) if in_dict == ORDER_DATE else key

    return sorted(posts, key=sort_key, reverse=by_full.startswith("desc_"))
