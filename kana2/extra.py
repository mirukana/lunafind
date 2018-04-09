"""Add extra informations to post dicts"""

import logging

import arrow
from whratio import ratio_float, ratio_int

from . import CLIENT, errors, reqwrap, utils

DL_INFO_KEYS = ("kana2_dl_url", "kana2_dl_ext", "kana2_dl_size",
                "kana2_is_ugoira")
RATIO_KEYS  = ("kana2_ratio_int", "kana2_ratio_float")
OTHER_KEYS  = ("kana2_fetch_date",)
KEYS        = DL_INFO_KEYS + RATIO_KEYS + OTHER_KEYS


def add_keys_if_needed(post):
    try:
        # If not "all those keys present in post"
        if not set(RATIO_KEYS) <= set(post):
            post = add_aspect_ratio(post)
    except errors.AddExtraKeyError as err:
        utils.log_error(err)

    try:
        if not set(DL_INFO_KEYS) <= set(post):
            post = add_dl_info(post)
    except errors.AddExtraKeyError as err:
        utils.log_error(err)

    if "kana2_fetch_date" not in post:
        post = add_date(post)

    return post


def add_aspect_ratio(post):
    try:
        k = RATIO_KEYS
        post[k[0]] = ratio_int(post["image_width"], post["image_height"])
        post[k[1]] = ratio_float(post["image_width"], post["image_height"])
        return post

    except KeyError as err:
        cannot = "%s and %s" % (k[0], k[1])
        raise errors.AddExtraKeyError(post, err.args[0], cannot)


def add_dl_info(post):
    try:
        k = DL_INFO_KEYS
        post[k[0]], post[k[1]], post[k[2]], post[k[3]] = get_dl_info(post)
        return post

    except errors.CriticalKeyError as err:
        cannot = "%s, %s, %s and %s" % (k[0], k[1], k[2], k[3])
        raise errors.AddExtraKeyError(post, err.missing_key, cannot)


def add_date(post, format_str="YYYY-MM-DDTHH:mm:ss.SSSZZ"):
    post["kana2_fetch_date"] = arrow.now().format(format_str)
    return post


def get_dl_info(post):
    try:
        url       = post["file_url"]
        ext       = url.split(".")[-1]
        size      = post.get("file_size", "no file_size key")
        is_ugoira = True if ext == "zip" else False
    except KeyError as err:
        raise errors.CriticalKeyError(post, err.args[0], print_err=False)

    if is_ugoira:
        try:
            url = post["large_file_url"]  # Video URL
            ext = url.split(".")[-1]
        except KeyError:
            logging.warning(
                "Post %s (ugoira) has no video, only ZIP will be retrievable.",
                post.get("id", "without ID")
            )

    # Only media hosted on raikou(2).donmai.us will have the full URL as value.
    url = url if url.startswith("http") else CLIENT.site_url + url

    if is_ugoira or size == "no file_size key":
        size = reqwrap.http("head", url).headers["content-length"]

    return url, ext, size, is_ugoira
