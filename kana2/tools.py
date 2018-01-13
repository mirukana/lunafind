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
        posts (list): Post dictionaries with non duplicated posts.

    Examples:
        >>> _json = tools.filter_duplicates([{"id": 1, ...},
                                            {"id": 1, ...},
                                            {"id": 2, ...}, ...])
        >>> _json
        [{'id': 1, ...}, {'id': 2, ...}, ...]

    """

    id_seen = [None]
    for i, post in enumerate(posts):
        if post["id"] in id_seen:
            del posts[i]
        else:
            id_seen.append(post["id"])
    return posts


def count_posts(tags=None):
    """Returns the quantity of posts of given tags.

    Args:
        tags (int or str): The desired tag(s) search. Default: None.

    Returns:
        (int) The number of existent posts with given tags.

    Examples:
        >>> tools.count_posts("hakurei_reimu")
        46343
        >>> tools.count_posts("hakurei_reimu maribel_hearn")
        342


        If it's given 2+ tags or an inexistent tag, it will return 0:

        >>> tools.count_posts("hakurei_reimy")
        0
        >>> tools.count_posts("hakurei_reimu maribel_hearn usami_renko")
        0


        If tags == None, it will return the total posts number in safebooru:

        >>> tools.count_posts()
        2236330
    """

    return exec_pybooru_call(CLIENT.count_posts, tags)["counts"]["posts"]


def exec_pybooru_call(function, *args, **kwargs):
    """Generates a dictionary containing general posts info.

    Args:
        function (function): The function to be used
        *args: What should be used as the function argument(s).

    Returns:
        If the rquest succeeds, it will return the function's output (usually
        a dictionary). Else it will raise an exception containing error
        information.

    Examples:
        >>> client = pybooru.danbooru.Danbooru("safebooru")
        >>> tools.exec_pybooru_call(CLIENT.count_posts, "hakurei_reimu")
        {'counts': {'posts': 46343}}

        >>> tools.exec_pybooru_call(CLIENT.note_show, 1667182)
        {'id': 1667182, 'created_at': '2016-05-10T06:58:29.587-04:00',
        'updated_at': '2016-05-10T06:58:29.587-04:00', 'creator_id': 327249,
        'x': 624, 'y': 199, 'width': 132, 'height': 153, 'is_active': True,
        'post_id': 2351910, 'body': 'Trying to get oxygen,', 'version': 1,
        'creator_name': 'Ph.D'}
    """

    for _ in range(1, 10 + 1):
        try:
            return function(*args, **kwargs)
        except (pybooru.exceptions.PybooruHTTPError, KeyError) as error:
            code = re.search(r"In _request: ([0-9]+)", error._msg).group(1)
            url = re.search(r"URL: (https://.+)", error._msg).group(1)
            logging.warning("Error %s from booru (URL: %s)", code, url)

    raise exceptions.QueryBooruError(code, url)


def generate_page_set(page_list, limit, total_posts):
    regexes = {
        "page-page": re.compile(r"^\d+-\d+$"),
        "page+": re.compile(r"^\d+\+$"),
        "+page": re.compile(r"^\+\d+$")
    }

    page_set = set()

    for page in page_list:
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
