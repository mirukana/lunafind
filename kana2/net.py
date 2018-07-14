"""Pybooru and requests lib call wrappers."""

import time

import pybooru

import requests

from . import errors, utils

# Don't waste time for errors that won't go away by retrying,
# like Unauthorized/Forbidden/Not Found/Invalid Parameters/etc.
FATAL_HTTP_CODES = (401, 403, 410, 404, 422, 423, 424)
MAX_TRIES        = 5


def boorify_url_params(params):
    new = {}
    for k, v in params.items():
        # Filter out "random" and "raw" parameters if their value is False
        # because Danbooru will see them as true (bug?).
        if not (k in ("random", "raw") and v is False):
            # Lowercase booleans:
            new[k] = "true" if v is True else "false" if v is False else v
    return new


def booru_api(function, *args, **kwargs):
    kwargs = boorify_url_params(kwargs)

    for tries in range(1, MAX_TRIES + 1):
        try:
            return function(*args, **kwargs)
        except pybooru.exceptions.PybooruHTTPError as err:
            code, url = err.args[1], err.args[2]

            if code in FATAL_HTTP_CODES:
                raise errors.RetryError(code, url, 1, 1, giving_up=True)

            try_again(code, url, tries)

    raise errors.RetryError(code, url, MAX_TRIES, MAX_TRIES, giving_up=True)


def http(method, url, session=requests.Session(), **kwargs):

    for tries in range(1, MAX_TRIES + 1):
        # e.g. http("get", ...) calls session.get(...)
        req  = getattr(session, method)(url, timeout=6, **kwargs)
        code = req.status_code

        if req.status_code in range(200, 204 + 1):
            return req

        if req.status_code in FATAL_HTTP_CODES:
            raise errors.RetryError(code, url, 1, 1, giving_up=True)

        try_again(code, url, tries)

    raise errors.RetryError(code, url, MAX_TRIES, MAX_TRIES, giving_up=True)


def try_again(code, url, tries, max_tries=MAX_TRIES):
    utils.log_error(errors.RetryError(code, url, tries, max_tries))
    time.sleep(get_retrying_in_time(tries))


def get_retrying_in_time(tries):
    # Example for 5 tries: 1st: 2s, 2nd: 4s, 3-5th: 6s
    return 6 if tries * 2 > 6 else tries * 2
