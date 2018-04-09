"""Easily download multiple posts"""
import json
import logging
import multiprocessing
import os
import shutil
import sys
from itertools import product

from pybooru.exceptions import PybooruError

from requests.exceptions import RetryError

from . import PROCESSES, errors, extra, media, tools, utils


def posts(posts_, dests=None, save_extra_info=True, stop_on_err=False):
    stats = {"total": len(posts_), "size":  get_dl_size(posts_)}

    logging.info("Downloading %d posts, estimated %s",
                 stats["total"], utils.bytes2human(stats["size"]))

    with multiprocessing.Pool(PROCESSES) as pool:
        returns = pool.starmap(
            one_post,
            product(posts_, (dests,), (save_extra_info,), (stop_on_err,))
        )

    stats["total_ok"]   = len([r for r in returns if r[1] is True])
    stats["total_fail"] = stats["total"] - stats["total_ok"]
    stats["successes"]  = dict(returns)

    return stats


def one_post(post, dests=None, save_extra_info=True, stop_on_err=False):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    post     = extra.add_keys_if_needed(post)
    dests    = dests or {}
    err_strs = []

    # Build the dests dict, with a default path if a key wasn't already
    # supplied. Make necessary directories.
    # False supplied = don't get this resource for posts.
    for res in ("media", "info", "notes", "artcom"):
        if dests.get(res) is False:
            continue

        default    = "{id}.{kana2_dl_ext}" if res == "media" else "{id}.json"
        default    = "%s%s%s" % (res, os.sep, default)
        dests[res] = tools.replace_keys(post, dests.get(res, default))

        os.makedirs(os.path.split(dests[res])[0], exist_ok=True)

    if dests["info"] is not False:
        dump = {k: v for k, v in post.items() if not k in extra.KEYS} \
               if not save_extra_info else post

        utils.chunk_write(json.dumps(dump, ensure_ascii=False, sort_keys=True),
                          dests["info"])
        del dump

    if dests["media"] is not False:
        try:
            utils.chunk_write(media.media(post), dests["media"], mode="wb")
            media.verify(post, dests["media"])

        except (errors.Kana2Error, PybooruError, RetryError) as err:
            err_strs.append(utils.log_error(err))

            if os.path.isfile(dests["media"]):
                logging.info("Moving failed post %s's media to %s",
                             post.get("id", "without ID"),
                             get_failed_dest(dests["media"]))
                move_failed(dests["media"])

            if stop_on_err:
                raise err

            return post.get("id"), err_strs

    #if dests["notes"] is not False: TODO
        #utils.chunk_write(notes.notes(post), dests["notes"])

    #if dests["artcom"] is not False: TODO
        #utils.chunk_write(artcom.artcom(post), dests["artcom"])

    # Cleanup empty dirs.
    for _, dest_path in dests.items():
        try:
            os.rmdir(os.path.split(dest_path)[0])
        except OSError:
            pass

    return post.get("id"), True


def get_dl_size(posts_):
    return sys.getsizeof(posts_) + sum(post["file_size"] for post in posts_)


def get_failed_dest(original_dest):
    dirs, file_ = os.path.split(original_dest)
    return "{0}{1}failed{1}{2}".format(dirs, os.sep, file_)


def move_failed(original_dest):
    new_path = get_failed_dest(original_dest)
    os.makedirs(os.path.split(new_path)[0], exist_ok=True)
    shutil.move(original_dest, new_path)
