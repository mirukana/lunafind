# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import re
import shlex
from typing import Generator, Sequence, Set

import arrow

from . import utils
from .post import Post

META_NUM_TAGS = {
    "width":    ["image_width",         int],
    "height":   ["image_height",        int],
    "mpixels":  ["mpixels",             float],  # millions of pixels
    "score":    ["score",               int],
    "favcount": ["fav_count",           int],
    "id":       ["id",                  int],
    "pixiv":    ["pixiv_id",            int],
    "pixiv_id": ["pixiv_id",            int],
    "tagcount": ["tag_count",           int],
    "gentags":  ["tag_count_general",   int],
    "arttags":  ["tag_count_artist",    int],
    "chartags": ["tag_count_character", int],
    "copytags": ["tag_count_copyright", int],
    "metatags": ["tag_count_meta",      int],
    "date":     ["created_at",
                 lambda v: arrow.get(v).replace(tzinfo="local").to("UTC-4")],
    # Non-standard addition: supports int:int *and* float ratio.
    "ratio":    ["ratio_float", utils.ratio2float],
    # Non-standard addition: supports microseconds and more units aliases.
    "age": ["created_at",  utils.age2date, "reverse_cmp"],
    # none, any, or the post number the post should be a child of.
    "parent": ["parent_id", int],
    # none, any, or (non-standard) a number of possessed children.
    "child": ["children_num", int],
    # Non-standard addition: supports units other than b/KB/MB
    "filesize": ["file_size", utils.human2bytes, "eq_fuzzy_20"],
    # Non-standard tags:
    "dlsize": ["dl_size", utils.human2bytes]
}


def _source_match(post: Post, value: str) -> bool:
    info_v = post.info["source"]

    if value == "none":
        return not info_v

    if value.startswith("pixiv/"):
        # If no / at the end, will match artists *starting with* value.
        return re.match(rf".*pixiv(\.net/img.*(/img)?)?/{value[6:]}.*", info_v,
                        re.IGNORECASE)

    # Other "source:..." on Danbooru: "match anything that starts with ...".
    # * in value = .* regex (other regexes get escaped).
    return re.match(r"%s.*" % re.escape(value).replace(r"\*", r".*"), info_v,
                    re.IGNORECASE)


META_STR_TAGS_FUNCS = {
    "md5":        lambda p, v: p.info["md5"]          == v,
    "filetype":   lambda p, v: p.info.get("file_ext") == v,
    "dltype":     lambda p, v: p.info.get("dl_ext")   == v,  # non-standard
    "rating":     lambda p, v: p.info["rating"].startswith(v),
    "locked":     lambda p, v: p.info[f"is_{v}_locked"],
    "status":     lambda p, v: v in ("any", "all") or p.info[f"is_{v}"],
    "source":     _source_match,
    "order":      None,
}


def _tag_present(post: Post, tag: str) -> bool:
    # Non-standard: support wildcards in "-tag" or "~tag".
    # "*" in tag → ".*?" regex, escape other regex/special chars
    # wrap strings in spaces to match tags even if they're at start/end.
    return re.match(r" %s " % re.escape(tag).replace(r"\*", r".*?"),
                    r" %s " % post.info["tag_string"],
                    re.IGNORECASE)


def _meta_num_match(post:Post, tag: str, value: str) -> bool:
    def compare(convert, info_v, value, eq_fuzzy_20, reverse_cmp) -> bool:
        # Non-standard: any/none supported for all meta numeric tags.
        if value == "none":
            return bool(not info_v)

        if value == "any":
            return bool(info_v)

        if value.startswith(">="):
            return info_v >= convert(value[2:])
        if value.endswith(".."):
            return info_v >= convert(value[:-2])

        if value.startswith("<=") or value.startswith(".."):
            return info_v <= convert(value[2:])

        if value.startswith(">"):
            return info_v > convert(value[1:])

        if value.startswith("<"):
            return info_v < convert(value[1:])

        if ".." in value:
            begin, end = value.split("..", maxsplit=1)

            if reverse_cmp:
                begin, end = end, begin
                return not convert(begin) <= info_v <= convert(end)

            return convert(begin) <= info_v <= convert(end)

        if "," in value:
            if not eq_fuzzy_20:
                return str(info_v) in value.split(",")

            return bool([v for v in value.split(",") if
                         v - v / 20 <= info_v <= v + v / 20])


        try:
            value = convert(value)

            if eq_fuzzy_20:
                # For filesize, it's what Danbooru does apparently
                # (not sure if this is the exact formula but close enough?).
                return value - value / 20 <= info_v <= value + value / 20

            return info_v == value
        except Exception:
            pass

        raise ValueError(f"Invalid search term value: '{tag}:{value}'.")

    convert     = META_NUM_TAGS[tag][1]
    info_v      = convert(post.info[META_NUM_TAGS[tag][0]])
    eq_fuzzy_20 = "eq_fuzzy_20" in META_NUM_TAGS[tag]
    reverse_cmp = "reverse_cmp" in META_NUM_TAGS[tag]

    result = compare(convert, info_v, value, eq_fuzzy_20, reverse_cmp)
    return result if not reverse_cmp else not result


def _filter_post(post:           Post,
                 simple_tags:    Set[str],
                 meta_num:       Set[str],
                 meta_str:       Set[str]) -> bool:

    no_prefix = lambda tag: tag[1:] if tag[0] in ("-", "~") else tag
    presences    = {}

    for tag in simple_tags:
        presences[tag] = _tag_present(post, no_prefix(tag))

    for tag_val in meta_num:
        tag, value         = tag_val.split(":", maxsplit=1)
        presences[tag_val] = _meta_num_match(post, no_prefix(tag), value)

    for tag_val in meta_str:
        tag, value         = tag_val.split(":", maxsplit=1)
        presences[tag_val] = META_STR_TAGS_FUNCS[no_prefix(tag)](post, value)

    tilde_tag_in_search   = False
    one_tilde_tag_present = False

    for term, present in presences.items():
        if term[0] == "-" and present:
            return False

        if term[0] not in ("-", "~") and not present:
            return False

        if term[0] == "~":
            tilde_tag_in_search = True

            if present:
                one_tilde_tag_present = True

    if tilde_tag_in_search and not one_tilde_tag_present:
        return False

    return True


def search(posts: Sequence[Post], terms: str) -> Generator[Post, None, None]:
    def raw_tag(term: str) -> str:
        tag = term.split(":")[0]
        return tag[1:] if tag[0] in ("-", "~") else tag

    terms     = set(shlex.split(terms))
    meta_num  = set(t for t in terms if raw_tag(t) in META_NUM_TAGS)
    meta_str  = set(t for t in terms if raw_tag(t) in META_STR_TAGS_FUNCS)
    tags      = terms - set(meta_num) - set(meta_str)

    term_args = (tags, meta_num, meta_str)

    for post in posts:
        if _filter_post(post, *term_args):
            yield post


# CHOICES = {
    # "order": {
        # ("id", "id_asc"),
        # "id_desc",
        # ("score", "score_desc"),
        # "score_asc",
        # "favcount",
        # "favcount_asc",
        # ("change", "change_desc"),
        # "change_asc",
        # ("comment", "comm"),
        # ("comment_asc", "comm_asc"),
        # "note",
        # "note_asc",
        # "artcomm",
        # ("mpixels", "mpixels_desc"),
        # "mpixels_asc",
        # "portrait",
        # "landscape",
        # ("filesize", "filesize_desc"),
        # "filesize_asc",
        # "rank",
        # "random"
    # }
# }
