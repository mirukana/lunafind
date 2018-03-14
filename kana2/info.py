"""Get booru post information from a query dictionary."""

import logging
import os

import arrow

from . import CLIENT, tools, utils, query

# TODO: Update docstrings
# TODO: multiprocessing

def info(queries, add_extra_info=True):
    for subquery in query.get_single_page_queries(queries):
        logging.info(
            "Getting info - tags: %s, page: %s, total: %s, "
            "posts: %s, limit: %s%s%s",
            subquery["tags"], subquery["page"], subquery["total_pages"],
            subquery["posts_to_get"], subquery["limit"],
            ", random" if subquery["random"] else "",
            ", raw"    if subquery["raw"]    else "")

        for post in tools.exec_pybooru_call(CLIENT.post_list, **subquery):
            if add_extra_info:
                post = extra_info(post)

            yield post


def extra_info(post):
    post["kana2_aspect_ratio"] = utils.get_ratio(post["image_width"],
                                                 post["image_height"])

    if post["file_ext"] == "zip":
        # File is ugoira, the webm is to be downloaded instead.
        post["kana2_ext"] = os.path.splitext(post["large_file_url"])[1][1:]
    else:
        post["kana2_ext"] = post["file_ext"]

    post["kana2_fetch_date"] = arrow.now().format("YYYY-MM-DDTHH:mm:ss.SSSZZ")

    return post
