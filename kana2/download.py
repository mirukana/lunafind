"""Easily download multiple posts"""
import logging
import os
import shutil
import sys
from itertools import product

import pybooru
from pybooru.exceptions import PybooruError

from requests.exceptions import RequestException
from requestspool import RequestsPool

from . import (CLIENT, PROCESSES, artcom, errors, extra, media, notes, tools,
               utils)


def posts(posts_, dests=None, save_extra_info=True, stop_on_err=False,
          clean=True):
    stats = {"total": len(posts_), "size":  get_dl_size(posts_)}

    logging.info("Downloading %d posts, estimated %s",
                 stats["total"], utils.bytes2human(stats["size"]))

    # client will be passed by RequestsPool.
    args_list         = list(product(posts_, (dests,), (save_extra_info,),
                                     (stop_on_err,), (False,)))

    # Cleanup dirs after finishing the last post, instead of trying every time.
    if clean:
        args_list[-1]     = list(args_list[-1])
        args_list[-1][-1] = True

    with RequestsPool(PROCESSES, pybooru.Danbooru, ("safebooru",)) as pool:
        returns = pool.starmap(one_post, args_list)

    stats["total_ok"]   = len([r for r in returns if r[1] is True])
    stats["total_fail"] = stats["total"] - stats["total_ok"]
    stats["returns"]    = dict(returns)

    return stats


def one_post(post, dests=None, save_extra_info=True, stop_on_err=False,
             clean=True, client=CLIENT):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    post          = extra.add_keys_if_needed(post, client)
    dests         = dests or {}
    errors_gotten = []

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
        # Remove extra info if save_extra_info is True
        dump = {k: v for k, v in post.items() if not k in extra.KEYS} \
               if not save_extra_info else post

        utils.chunk_write(utils.jsonify(dump), dests["info"])
        del dump

    if dests["media"] is not False:
        try:
            utils.chunk_write(media.media(post, client=client), dests["media"],
                              mode="wb")
            media.verify(post, dests["media"], client)

        except (errors.Kana2Error, PybooruError, RequestException) as err:
            utils.log_error(err)
            # Append dict containing error attributes and error name.
            errors_gotten.append({**vars(err),
                                  **{"error": err.__class__.__name__}})

            if os.path.isfile(dests["media"]):
                logging.info("Moving failed post %s's media to %s",
                             post.get("id", "without ID"),
                             get_failed_dest(dests["media"]))
                move_failed(dests["media"])

            if stop_on_err:
                raise err

            return post.get("id"), errors_gotten

    def write_notes_or_artcom(resource, content):
        if dests[resource] is not False and content and content != []:
            utils.chunk_write(utils.jsonify(content), dests[resource])

    write_notes_or_artcom("notes", notes.notes(post, client=client))
    write_notes_or_artcom("artcom", artcom.artcom(post, client=client))

    if clean:
        cleanup(dests)

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


def cleanup(dests):
    # TODO: Check if other subprocesses are still running before doing this.
    for _, dest_path in dests.items():
        try:
            os.rmdir(os.path.split(dest_path)[0])
        except OSError:
            pass
