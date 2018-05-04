"""Get booru post information from a query dictionary."""

import logging
from itertools import product

import pybooru

from requestspool import RequestsPool

from . import CLIENT, PROCESSES, errors, extra, reqwrap, utils


def pages(queries, add_extra_info=True, stop_on_err=False):
    with RequestsPool(PROCESSES, pybooru.Danbooru, ("safebooru",)) as pool:
        # starmap() will see a list of (a_query, add_extra_info) tuples,
        # each corresponding to the params for a one_page() function call.
        # >>> list(product([1,2,3], (True,)))
        # [(1, True), (2, True), (3, True)]
        return utils.flatten_list(
            pool.starmap(one_page_handle_err,
                         product(queries, (add_extra_info,), (stop_on_err,))))


def one_page_handle_err(query, add_extra_info=True, stop_on_err=False,
                        client=CLIENT):
    try:
        return one_page(query, add_extra_info, client)
    except errors.Kana2Error as err:
        utils.log_error(err)

        if stop_on_err:
            raise err

        return []


def one_page(query, add_extra_info=True, client=CLIENT):
    if not isinstance(query, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(query))

    # e.g. Retrieving info - tags: rumia, page: 1, limit: 200, ...
    logging.info("Retrieving info - %s", str(query).replace("'", "")[1:-1])

    return [extra.add_keys_if_needed(post, client) if add_extra_info else post
            for post in reqwrap.pybooru_api(client.post_list, **query)]
