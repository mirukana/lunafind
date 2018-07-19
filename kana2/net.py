"""Pybooru and requests lib call wrappers."""

import logging as log

import pybooru
from pybooru.exceptions import PybooruError, PybooruHTTPError
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES
from urllib3.util import Retry

from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import config

# Missing in Pybooru. Usually Cloudflare saying the target site is down.
BOORU_CODES[502] = ("Bad Gateway",
                    "Invalid response from the server to the gateway.")

BOORU_CODE_GROUPS = {"OK":    (200, 201, 202, 204),
                     "Retry": (420, 421, 429, 500, 502, 503),
                     "Fatal": (400, 401, 403, 404, 410, 422, 423, 424)}

RETRY = Retry(total=4,
              status_forcelist=BOORU_CODE_GROUPS["Retry"],
              backoff_factor=1.5,
              raise_on_redirect=False,
              raise_on_status=False,
              respect_retry_after_header=True)

def get_booru_client(site_name="", site_url="", username="", api_key=""):
    client = pybooru.Danbooru(site_name, site_url, username, api_key)

    # Requests Session, alias for the confusing attribute name.
    client.session = client.client

    for protocol in ("http://", "https://"):
        client.session.mount(protocol, HTTPAdapter(max_retries=RETRY))
    return client


def boorify_url_params(params):
    new = {}
    for k, v in params.items():
        # Filter out "random" and "raw" parameters if their value is False
        # because Danbooru will see them as true (bug on their side probably).
        if not (k in ("random", "raw") and v is False):
            # Lowercase booleans:
            new[k] = "true" if v is True else "false" if v is False else v
    return new


def booru_api(client_method, *args, **kwargs):
    try:
        return client_method(*args, **boorify_url_params(kwargs))

    except PybooruHTTPError as err:
        code = BOORU_CODES[err.args[1]]
        log.error(f"{err.args[1]}: {code[0]} - {code[1]} - URL: {err.args[2]}")

    except (PybooruError, RequestException) as err:
        log.error(str(err))

    return []


def http(method, url, session=None, **kwargs):
    # Can't put default in function definition, AttributeError.
    session = session or config.CLIENT.session

    try:
        req = session.request(method, url, timeout=6.5, **kwargs)
    except RequestException as err:
        log.error(str(err))

    if req.status_code in BOORU_CODE_GROUPS["OK"]:
        return req

    code = BOORU_CODES[req.status_code]
    log.error(f"{req.codeus_code}: {code[0]}, {code[1]} - URL: {req.url}")
    return []
