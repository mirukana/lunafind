import logging
import math
import re

import pybooru

from . import tools
from .. import exceptions

from . import client


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


def generate_page_set(page_iter, tags, limit, total_posts):
    regexes = {
        "page-page": re.compile(r"^\d+-\d+$"),
        "page+": re.compile(r"^\d+\+$"),
        "+page": re.compile(r"^\+\d+$")
    }

    page_set = set()

    for page in page_iter:
        page = str(page)

        if page.isdigit():
            page_set.add(int(page))
            continue

        # e.g. -p 3-10: All the pages in the range (3, 4, 5...).
        if regexes["page-page"].match(page):
            begin = int(page.split("-")[0])
            end = int(page.split("-")[-1])

        # e.g. -p 2+: All the pages in a range from 2 to the last possible.
        elif regexes["page+"].match(page):
            begin = int(page.split("+")[0])
            end = math.ceil(total_posts / limit)

        # e.g. -p +5: All the pages in a range from 1 to 5.
        elif regexes["+page"].match(page):
            begin = 1
            end = int(page.split("+")[-1])

        page_set.update(range(begin, end + 1))

    return page_set
