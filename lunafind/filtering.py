# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import re
import shlex
from typing import Generator, Iterable, Optional, Set, Union

import pendulum as pend

import whratio
# pylint: disable=no-name-in-module
from fastnumbers import fast_float, fast_int

from . import LOG, utils
from .clients.base import InfoType
from .post import Post


def parse_date(value) -> pend.DateTime:
    # tz="local" only applies if there's no tz in the value
    return pend.parse(value, tz="local")


def safe_int(value) -> int:
    return fast_int(value, 0)


META_NUM_TAGS = {
    "width":    ["image_width",         safe_int],
    "height":   ["image_height",        safe_int],
    "score":    ["score",               safe_int],
    "favcount": ["fav_count",           safe_int],
    "id":       ["id",                  safe_int],
    "pixiv":    ["pixiv_id",            safe_int],
    "tagcount": ["tag_count",           safe_int],
    "gentags":  ["tag_count_general",   safe_int],
    "arttags":  ["tag_count_artist",    safe_int],
    "chartags": ["tag_count_character", safe_int],
    "copytags": ["tag_count_copyright", safe_int],
    "metatags": ["tag_count_meta",      safe_int],
    "date":     ["created_at",          parse_date],

    "mpixels": [lambda i: (safe_int(i["image_width"]) *
                           safe_int(i["image_height"])) / 1_000_000,
                fast_float],

    # Non-standard addition: support both float and int:int user ratios.
    "ratio":    [lambda i: whratio.as_float(fast_int(i["image_width"],  1),
                                            fast_int(i["image_height"], 1)),
                 utils.ratio2float],

    # Non-standard addition: supports microseconds and more units aliases.
    "age": ["created_at",  utils.age2date, "reverse_cmp"],
    # none, any, or the post number the post should be a child of.
    "parent": ["parent_id", fast_int],
    # none, any, or (non-standard) a number of possessed children.
    "child": [lambda i: len((i["children_ids"] or "").split()), safe_int],
    # Non-standard addition: supports units other than b/KB/MB
    "filesize": ["file_size", utils.human2bytes, "eq_fuzzy_20"],

    "fetch":    ["fetched_at", parse_date],
    "fetchage": ["fetched_at", utils.age2date, "reverse_cmp"],
}


def _source_match(info: InfoType, value: str, key: str = "source") -> bool:
    if value == "none":
        return not info[key]

    if value.startswith("pixiv/"):
        # If no / at the end, will match artists *starting with* value.
        return re.search(rf"pixiv(\.net/img.*(/img)?)?/{value[6:]}",
                         info[key], re.IGNORECASE)

    # Other "source:..." on Danbooru: "match anything that starts with ...".
    # * in value = .* regex (other regexes get escaped).
    return re.match(r"%s.*" % re.escape(value).replace(r"\*", r".*"),
                    info[key], re.IGNORECASE)


META_STR_TAGS_FUNCS = {
    "md5":      lambda info, v: info["md5"]          == v,
    "filetype": lambda info, v: info.get("file_ext") == v,
    "rating":   lambda info, v: info["rating"][0]    == v[0],
    "locked":   lambda info, v: info[f"is_{v}_locked"],
    "status":   lambda info, v: v in ("any", "all") or info[f"is_{v}"],
    "source":   _source_match,

    # Non-standard tags:
    "from": lambda info, v: info["fetched_from"] == v,
}


def _tag_present(info: InfoType, tag: str) -> bool:
    # Avoid regex unless no choice, they have bad performances.
    # Wrap strings in spaces to match tags even if they're at start/end.
    if "*" not in tag:
        return f" {tag} " in f" {info['tag_string']} "

    if tag == "*":
        return True

    if "*" in tag and "*" not in tag[1:-1]:
        tag = f"{tag[1:]}"  if tag[0]  == "*" else f" {tag}"
        tag = f"{tag[:-1]}" if tag[-1] == "*" else f"{tag} "
        return tag in f" {info['tag_string']} "

    # Non-standard: support wildcards in "-tag" or "~tag".
    # "*" in tag → ".*?" regex, escape other regex/special chars
    return re.search(r" %s " % re.escape(tag).replace(r"\*", r".*?"),
                     r" %s " % info["tag_string"],
                     re.IGNORECASE)


def _meta_num_match(info: InfoType, tag: str, value: str) -> bool:
    convert = META_NUM_TAGS[tag][1]

    info_v = META_NUM_TAGS[tag][0]
    info_v = convert(
        info_v(info) if callable(META_NUM_TAGS[tag][0]) else info[info_v]
    )

    eq_fuzzy_20 = "eq_fuzzy_20" in META_NUM_TAGS[tag]
    reverse_cmp = "reverse_cmp" in META_NUM_TAGS[tag]

    def compare(convert, info_v, value, eq_fuzzy_20, reverse_cmp) -> bool:
        # Non-standard: none/any supported for all meta numeric tags.
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

    result = compare(convert, info_v, value, eq_fuzzy_20, reverse_cmp)
    return result if not reverse_cmp else not result


def _filter_info(info:        InfoType,
                 simple_tags: Set[str],
                 meta_num:    Set[str],
                 meta_str:    Set[str]) -> bool:

    no_prefix = lambda tag: tag[1:] if tag[0] in ("-", "~") else tag
    presences    = {}

    for tag in simple_tags:
        presences[tag] = _tag_present(info, no_prefix(tag))

    for tag_val in meta_num:
        tag, value         = tag_val.split(":", maxsplit=1)
        presences[tag_val] = _meta_num_match(info, no_prefix(tag), value)

    for tag_val in meta_str:
        tag, value         = tag_val.split(":", maxsplit=1)
        presences[tag_val] = META_STR_TAGS_FUNCS[no_prefix(tag)](info, value)

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


def filter_all(items:         Iterable[Union[InfoType, Post]],
               terms:         str,
               raw:           bool = False,
               stop_on_match: bool = False,
               partial_tags:  bool = False,
              ) -> Generator[Union[InfoType, Post], None, int]:

    def raw_tag(term: str) -> Optional[str]:
        if not ":" in term:
            return None
        tag = term.split(":")[0]
        return tag[1:] if tag[0] in ("-", "~") else tag

    terms     = set(shlex.split(terms.lower())) if not raw else {terms.lower()}
    meta_num  = set(t for t in terms if raw_tag(t) in META_NUM_TAGS)
    meta_str  = set(t for t in terms if raw_tag(t) in META_STR_TAGS_FUNCS)
    tags      = terms - set(meta_num) - set(meta_str)

    if partial_tags:
        tags = {re.sub(r"^(-|~)?(.+)", r"\1*\2*", t) for t in tags}

    term_args = (tags, meta_num, meta_str)

    discarded = 0

    for item in items:
        info = item.info if isinstance(item, Post) else item

        try:
            if stop_on_match:
                if not _filter_info(info, *term_args):
                    yield item
                else:
                    return 0

            else:
                if _filter_info(info, *term_args):
                    yield item
                else:
                    discarded += 1

        except KeyError as err:
            LOG.warning("No %r key for post %d.", err.args[0], info["id"])

    return discarded
