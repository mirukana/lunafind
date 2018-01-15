"""Various global variables, functions and others specially used for kana2."""

import logging
import shutil

import pybooru

from . import utils

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


def get_file_to_dl_ext(post):
    # TODO: Config option to download normal zip instead.
    try:
        if post["file_url"].endswith(".zip"):
            return post["large_file_url"].split(".")[-1]
        return post["file_ext"]
    except KeyError:
        return "unknown"


def has_vital_keys(post, action, keys=["id"]):
    id_str = ""
    if "id" in post:
        id_str = " %s" % post["id"]

    for key in keys:
        if key not in post:
            logging.error("Unable to %s for post%s, missing %s",
                          action, id_str, key)
            if "id" in post:
                move_failed_dl(post["id"],
                               get_file_to_dl_ext(post),
                               "missing-" + key)
            return False


def move_failed_dl(post_id, media_ext, error_dir):
    media = "media/", "%s.%s" % (post_id, media_ext)
    info = "info/", "%s.json" % post_id

    for path in media, info:
        utils.make_dirs("%s/%s" % (path[0], error_dir))
        try:
            dir_file = "".join(path)
            shutil.move(dir_file, dir_file.replace("/", "/%s/" % error_dir, 1))
        except FileNotFoundError:
            pass
