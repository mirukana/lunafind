"""Various global variables, functions and others specially used for kana2."""

import logging
import math
import re

import pybooru

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
        tags (str, optional): The desired tag search to get a count for.
            If this is None, the post count for the entire booru will be shown.
            Default: None.

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
        BooruError: If giving up after too many errors.

    Examples:
        >>> import pybooru
        >>> client = pybooru.danbooru.Danbooru("safebooru")
        >>> tools.exec_pybooru_call(client.count_posts, "hakurei_reimu")
        {'counts': {'posts': ...}}

        >>> tools.exec_pybooru_call(client.post_show, -1)
        WARNING:root:Error 404 from booru (URL: https://.../posts/-1.json)
        ...
        kana2.exceptions.BooruError: Unable to complete request,
...         error 404 from 'https://safebooru.donmai.us/posts/-1.json'.
    """

    for _ in range(1, 10 + 1):
        try:
            return function(*args, **kwargs)
        except pybooru.exceptions.PybooruHTTPError as error:
            code, url = error.args[1], error.args[2]
            logging.warning("Error %s from booru - URL: %s", code, url)

    raise pybooru.exceptions.PybooruHTTPError(
        'Unable to complete request after 10 tries', code, url)


def generate_page_set(pages, total_posts=None, limit=None):
    """Return a set of valid booru pages from a list of expressions.

    An expression can be a:
    - Single page (e.g. `"1"`);
    - Range (`"3-5"`);
    - Range from the first page to a given page (`"+6"`);
    - Range from the a given page to the last page (`"1+"`).

    Args:
        pages (list): Page expressions to parse.
        total_posts (int, optional): Total number of posts for the tag search
            pages are generated for.  Needed for `"<page>+"` expressions.
            Defaults to `None`.
        limit (int, optional): Number of posts per page.
            Needed for `"<page>+"` expressions.  Defaults to `None`.

    Raises:
        TypeError: If a `"<page>+"` item is present in `pages`, but
                   the `limit` or `total_posts` parameter isn't set.

    Examples:
        >>> tools.generate_page_set(["20", "7", "6-9", "+3"])
        {1, 2, 3, 6, 7, 8, 9, 20}

        >>> tools.generate_page_set(["1+"])
        ...
        TypeError: limit and total_posts parameters required to use the
...                <page>+ feature.

        >>> tools.generate_page_set(["1+"], tools.count_posts("ib"), 200)
        {1, 2, 3, 4, 5, 6}
    """
    page_set = set()

    for page in pages:
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
