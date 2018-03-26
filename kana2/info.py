"""Get booru post information from a query dictionary."""

import logging
# Using threads instead of processes, else SSL errors happen.
from multiprocessing.dummy import Pool as ThreadPool
import os

import arrow

from . import CLIENT, PROCESSES, tools, utils


def pages(queries, add_extra_info=True):
    with ThreadPool(PROCESSES) as pool:
        return utils.flatten_list(pool.map(one_page, queries))


def one_page(query, add_extra_info=True):
    if not isinstance(query, dict):
        raise TypeError("Expected one query dictionary, got %s" % type(query))

    logging.info("Getting info - tags: %s, page: %s, total: %s, "
                 "limit: %s, posts: %s%s%s",
                 query["tags"], query["page"], query["total_pages"],
                 query["limit"], query["posts_to_get"],
                 ", random" if query["random"] else "",
                 ", raw"    if query["raw"]    else "")

    return [extra_info(post) if add_extra_info else post
            for post in tools.exec_pybooru_call(CLIENT.post_list, **query)]


def extra_info(post):
    post["kana2_aspect_ratio"] = utils.get_ratio(post["image_width"],
                                                 post["image_height"])

    try:
        if post["file_ext"] == "zip":
            # File is ugoira, the webm is to be downloaded instead.
            post["kana2_ext"] = os.path.splitext(post["large_file_url"])[1][1:]
        else:
            post["kana2_ext"] = post["file_ext"]
    except KeyError:
        # TODO: general verify post function
        logging.error("Post %d is missing a file_ext key, "
                      "cannot add kana2_ext key", post["id"])

    post["kana2_fetch_date"] = arrow.now().format("YYYY-MM-DDTHH:mm:ss.SSSZZ")

    return post
