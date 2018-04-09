"""Get booru post information from a query dictionary."""

import logging
from itertools import product
from multiprocessing.dummy import Pool as ThreadPool

from . import CLIENT, PROCESSES, extra, reqwrap, utils


def pages(queries, add_extra_info=True):
    # Can't use multiprocessing without SSL errors, using
    # undocumented multithread Pools instead.
    with ThreadPool(PROCESSES) as pool:
        # starmap() will see a list of (a_query, add_extra_info) tuples,
        # each corresponding to the params for a one_page() function call.
        # >>> list(product([1,2,3], (True,)))
        # [(1, True), (2, True), (3, True)]
        return utils.flatten_list(
            pool.starmap(one_page, product(queries, (add_extra_info,)))
        )


def one_page(query, add_extra_info=True):
    if not isinstance(query, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(query))

    # e.g. Retrieving info - tags: rumia, page: 1, limit: 200, ...
    logging.info("Retrieving info - %s", str(query).replace("'", "")[1:-1])

    return [extra.add_keys_if_needed(post) if add_extra_info else post
            for post in reqwrap.pybooru_api(CLIENT.post_list, **query)]
