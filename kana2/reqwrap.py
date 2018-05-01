"""Pybooru and requests lib call wrappers"""

import logging
import time

import pybooru
from pybooru.resources import HTTP_STATUS_CODE as HTTP_BOORU_CODES

import requests


def pybooru_api(function, *args, **kwargs):
    """Retry a Pybooru function 5 times before giving up.

    `pybooru.exceptions.PybooruHTTPError` exceptions will be caught.

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
        >>> reqwrap.pybooru_api(client.count_posts, "hakurei_reimu")
        {'counts': {'posts': ...}}

        >>> reqwrap.pybooru_api(client.post_show, -1)
        WARNING:root:Error 404 from booru (URL: https://.../posts/-1.json)
        ...
        kana2.errors.BooruError: Unable to complete request,
...         error 404 from 'https://safebooru.donmai.us/posts/-1.json'.
    """

    # Build the actual parameter dict for the API query URL:
    # Filter out "random" and "raw" parameters if their value is False
    # because Danbooru will see them as true (bug?);
    # Filter out kana2-specific parameters like "posts_to_get";
    # Replace boolean parameters by lowercase strings equivalents
    # so they can be interpreted correctly by Danbooru.
    kwargs = {k: "true" if v is True else "false" if v is False else v
              for k, v in kwargs.items()
              if not (k in ("random", "raw") and v is False) and \
                 not k in ("posts_to_get", "total_pages", "type")}

    max_tries = 5

    for tries in range(1, max_tries + 1):
        try:
            return function(*args, **kwargs)
        except pybooru.exceptions.PybooruHTTPError as error:
            code, url = error.args[1], error.args[2]

            logging.error(get_error_msg(code, url, tries, max_tries))
            time.sleep(get_retrying_in_time(tries))

    raise pybooru.exceptions.PybooruError(get_fatal_msg(code, url, max_tries))


def http(method, url, session=requests.Session(), **kwargs):
    max_tries = 5

    for tries in range(1, max_tries + 1):
        # e.g. http("get", ...) calls session.get(...)
        req = getattr(session, method)(url, timeout=6, **kwargs)
        code = req.status_code

        if req.status_code in range(200, 204 + 1):
            return req

        logging.error(get_error_msg(code, url, tries, max_tries))
        time.sleep(get_retrying_in_time(tries))

    raise requests.exceptions.RetryError(get_fatal_msg(code, url, max_tries))


def get_retrying_in_time(tries):
    # Example for 5 tries: 1st: 2s, 2nd: 4s, 3-5th: 6s
    return 6 if tries * 2 > 6 else tries * 2


def get_error_msg(code, url, tries, max_tries):
    return ("Booru request error: %d - %s, %s - URL: %s - "
            "Retrying in %ss (%s/%s)." %
            (code, HTTP_BOORU_CODES[code][0], HTTP_BOORU_CODES[code][1], url,
             get_retrying_in_time(max_tries), tries, max_tries))


def get_fatal_msg(code, url, tried_times):
    return ("Request failed after %d tries: %d - %s, %s - URL: %s" %
            (tried_times, code,
             HTTP_BOORU_CODES[code][0], HTTP_BOORU_CODES[code][1], url))
