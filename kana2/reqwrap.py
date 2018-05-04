"""Pybooru and requests lib call wrappers"""

import logging
import time

import pybooru

import requests

from . import errors


def pybooru_api(function, *args, **kwargs):
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
            try_again(code, url, tries, max_tries)

    raise errors.RetryError(code, url, max_tries, max_tries, giving_up=True)


def http(method, url, session=requests.Session(), **kwargs):
    max_tries = 5

    for tries in range(1, max_tries + 1):
        # e.g. http("get", ...) calls session.get(...)
        req  = getattr(session, method)(url, timeout=6, **kwargs)
        code = req.status_code

        if req.status_code in range(200, 204 + 1):
            return req

        try_again(code, url, tries, max_tries)

    raise errors.RetryError(code, url, max_tries, max_tries, giving_up=True)


def try_again(code, url, tries, max_tries):
    logging.error(errors.RetryError(code, url, tries, max_tries).message)
    time.sleep(get_retrying_in_time(tries))


def get_retrying_in_time(tries):
    # Example for 5 tries: 1st: 2s, 2nd: 4s, 3-5th: 6s
    return 6 if tries * 2 > 6 else tries * 2
