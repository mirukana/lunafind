"""Get booru post information from a query dictionary."""

import logging
# Using threads instead of processes, else SSL errors happen.
from multiprocessing.dummy import Pool as ThreadPool
import os

import arrow

from . import CLIENT, PROCESSES, query, tools, utils


def pages(queries, add_extra_info=True):
    with ThreadPool(PROCESSES) as pool:
        yield pool.map(one_page,
                       query.get_single_page_queries(queries),
                       add_extra_info)


def one_page_pool(*args, **kwargs):
    yield list(one_page(*args, **kwargs))


def one_page(query_, add_extra_info=True):
    try:
        query_ = next(query_)
    except (TypeError, StopIteration):
        pass

    logging.info("Getting info - tags: %s, page: %s, total: %s, "
                 "limit: %s, posts: %s%s%s",
                 query_["tags"], query_["page"], query_["total_pages"],
                 query_["limit"], query_["posts_to_get"],
                 ", random" if query_["random"] else "",
                 ", raw"    if query_["raw"]    else "")

    for post in tools.exec_pybooru_call(CLIENT.post_list, **query_):
        yield extra_info(post) if add_extra_info else post


def extra_info(post):
    post["kana2_aspect_ratio"] = utils.get_ratio(post["image_width"],
                                                 post["image_height"])

    # TODO: Remove this try/except once the error has been caught.
    try:
        if post["file_ext"] == "zip":
            # File is ugoira, the webm is to be downloaded instead.
            post["kana2_ext"] = os.path.splitext(post["large_file_url"])[1][1:]
        else:
            post["kana2_ext"] = post["file_ext"]

        post["kana2_fetch_date"] = arrow.now().format("YYYY-MM-DDTHH:mm:ss.SSSZZ")
    except KeyError:
        from pprint import pprint
        pprint(post)
        raise

    return post
