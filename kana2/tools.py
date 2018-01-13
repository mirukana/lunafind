"""Tools used in internal scripts."""

import logging
import math
import re

import pybooru

from . import exceptions


CLIENT = pybooru.danbooru.Danbooru("safebooru")
"""pybooru.danbooru.Danbooru: See :class:`~pybooru.danbooru.Danbooru`"""


# TODO: Move this to filter.py
def filter_duplicates(posts):
    """Return a list of unique posts, duplicates are detected by post id.

    Args:
        posts (list): Post information dictionaries.

    Returns:
        posts (list): Post dictionaries without duplicates.

    Examples:
        >>> tools.filter_duplicates([{"id": 1}, {"id": 1}, {"id": 2}])
        [{'id': 1}, {'id': 2}]

    """

    id_seen = [None]
    for i, post in enumerate(posts):
        if post["id"] in id_seen:
            del posts[i]
        else:
            id_seen.append(post["id"])
    return posts


def count_posts(tags=None):
    """Return the number of posts for given tags.

    Args:
        tags (str): The desired tag search to get a count for. Default: None.
                    If this is None, the post count for the entire booru will
                    be shown.

    Returns:
        (int): The number of existing posts with given tags.
               If the number of tags used exceeds the maximum limit
               (2 for visitors and normal members on Danbooru), return `0`.

    Examples:
        >>> tools.count_posts() > 1000
        True

        >>> tools.count_posts("hakurei_reimu date:2017-09-17")
        5

        >>> tools.count_posts("hakurei_reimu maribel_hearn usami_renko")
        0
    """

    return exec_pybooru_call(CLIENT.count_posts, tags)["counts"]["posts"]


def exec_pybooru_call(function, *args, **kwargs):
    """Retry a Pybooru function 10 times before giving up.

    `pybooru.exceptions.PybooruHTTPError` and `KeyError` exceptions
    will be caught.

    Args:
        function (function): The function to be used.
        *args: Any function argument.
        **kwargs: Any named function argument.

    Returns:
        If the function succeeds, its output will be returned.

    Raises:
        QueryBooruError: If giving up after too many errors.

    Examples:
        >>> import pybooru
        >>> client = pybooru.danbooru.Danbooru("safebooru")
        >>> tools.exec_pybooru_call(client.count_posts, "hakurei_reimu")
        {'counts': {'posts': ...}}

        >>> tools.exec_pybooru_call(client.post_show, -1)
        WARNING:root:Error 404 from booru (URL: https://.../posts/-1.json)
        ...
        kana2.exceptions.QueryBooruError: Unable to complete request,
...         error 404 from 'https://safebooru.donmai.us/posts/-1.json'.
    """

    for _ in range(1, 10 + 1):
        try:
            return function(*args, **kwargs)
        except (pybooru.exceptions.PybooruHTTPError, KeyError) as error:
            code = re.search(r"In _request: ([0-9]+)", error._msg).group(1)
            url = re.search(r"URL: (https://.+)", error._msg).group(1)
            logging.warning("Error %s from booru (URL: %s)", code, url)

    raise exceptions.QueryBooruError(code, url)


def generate_page_set(page_list, limit=None, total_posts=None):
    page_set = set()

    for page in page_list:
        page = str(page)

        if page.isdigit():
            page_set.add(int(page))
            continue

        # e.g. -p 3-10: All the pages in the range (3, 4, 5...).
        if re.match(r"^\d+-\d+$", page):
            begin = int(page.split("-")[0])
            end = int(page.split("-")[-1])

        # e.g. -p 2+: All the pages in a range from 2 to the last possible.
        elif re.match(r"^\d+\+$", page):
            begin = int(page.split("+")[0])

            if not limit or not total_posts:
                raise TypeError("limit and total_posts parameters required "
                                "to use the <page>+ feature.")

            end = math.ceil(total_posts / limit)

        # e.g. -p +5: All the pages in a range from 1 to 5.
        elif  re.match(r"^\+\d+$", page):
            begin = 1
            end = int(page.split("+")[-1])

        page_set.update(range(begin, end + 1))

    return page_set
