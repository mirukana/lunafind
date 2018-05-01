"""Various global variables, functions and others specially used for kana2."""

import re

from . import CLIENT, reqwrap


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


def count_posts(tags=None, client=CLIENT):
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

    return reqwrap.pybooru_api(client.count_posts, tags)["counts"]["posts"]


def replace_keys(post, string):
    if not isinstance(string, str):
        return string

    # Unless \ escaped: {foo} → Capture foo; {foo, bar} Capture foo and bar.
    return re.sub(r"(?<!\\)(?:\\\\)*{(.+?)(?:, ?(.+?))?}",
                  lambda match: str(post.get(match.group(1), match.group(2))),
                  string)
