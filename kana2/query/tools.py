import logging
import re

import pybooru

from . import client
from .. import exceptions


# TODO: Move this to filter.py
def filter_duplicates(postsList):
    """Return a list of unique posts, duplicates are detected by post id."""
    idSeen = []
    for i, postDict in enumerate(postsList):
        if postDict["id"] in idSeen:
            del postsList[i]
        else:
            idSeen.append(postDict["id"])
    return postsList


def count_posts(tags=None):
    return exec_pybooru_call(client.count_posts, tags)["counts"]["posts"]


def exec_pybooru_call(function, *args, **kwargs):
    for max_error_count in range(1, 10 + 1):
        try:
            return function(*args, **kwargs)
        except (pybooru.exceptions.PybooruHTTPError, KeyError) as error:
            code = re.search(r"In _request: ([0-9]+)", error._msg).group(1)
            url = re.search(r"URL: (https://.+)", error._msg).group(1)
            logging.warn("Error %s from booru (URL: %s)" % (code, url))

    raise exceptions.QueryBooruError(code, url)
