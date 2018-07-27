"""Booru clients classes"""

import logging as log
import os
import re
from urllib.parse import parse_qs, urlparse

import pybooru
from pybooru.exceptions import PybooruError, PybooruHTTPError
from pybooru.resources import HTTP_STATUS_CODE as BOORU_CODES
from urllib3.util import Retry

from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from . import io, utils

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

class Danbooru(object):
    def __init__(self, name="safebooru", url="", username="", api_key=""):
        self.client = pybooru.Danbooru(name, url, username, api_key)
        self.url    = self.client.site_url
        self.name   = self.client.site_name or urlparse(self.url).netloc

        # Requests Session, alias for the confusing attribute name.
        self.client.session = self.client.client

        for scheme in ("http://", "https://"):
            self.client.session.mount(scheme, HTTPAdapter(max_retries=RETRY))

    # Display:

    def __repr__(self):
        return f"Danbooru(name='{self.name}', url='{self.url}')"

    def __str__(self):
        return str(self.__dict__)

    # Network requests:

    def api(self, client_function, *args, **kwargs):
        try:
            # TODO: catch invalid func
            client_function = getattr(self.client, client_function)
            return client_function(*args, **_format_url_params(kwargs))

        except PybooruHTTPError as e:
            code = e.args[1]
            short_desc, long_desc = BOORU_CODES[code]
            log.error(f"{code}: {short_desc} - {long_desc} - URL: {e.args[2]}")

        except (PybooruError, RequestException) as e:
            log.error(str(e))

        return []


    def http(self, http_method, url, **request_method_kwargs):
        try:
            result = self.client.session.request(
                http_method, url, timeout=6.5, **request_method_kwargs)
        except RequestException as e:
            log.error(str(e))

        code = result.status_code
        short_desc, long_desc = BOORU_CODES[code]

        if code in BOORU_CODE_GROUPS["OK"]:
            return result

        log.error(f"{code}: {short_desc}, {long_desc} - URL: {result.url}")
        return []

    # Get post info:

    def search(self, tags="", page=1, limit=200, random=False, raw=False):
        params = {"tags": tags}

        # Add other params only if search isn't just an ID or MD5.
        if not re.match(r"^(id|md5):[a-fA-F\d]+$", tags):
            params.update({"page": page, "limit": limit})
            if random:
                params["random"] = random
            if raw:
                params["raw"] = raw

        log.info("Retrieving post info - %s", utils.simple_str_dict(params))
        yield from self.api("post_list", **params)


    def info_id(self, id_):
        yield from self.search(tags=f"id:{id_}")


    def info_md5(self, md5):
        yield from self.search(tags=f"md5:{md5}")


    def info_post_url(self, url):
        id_ = re.search(r"/posts/(\d+)\??.*$", url).group(1)
        yield from self.info_id(id_)


    def info_search_url(self, url):
        params = parse_qs(urlparse(url).query)
        # No limit specified in url = 20 results, not 200;
        # we want to get exactly what the user sees on his browser.
        # limit parameter is extracted as a string in a list, don't know why.
        params["limit"] = int(params.get("limit")[0]) or 20

        yield from self.search(
            params.get("tags"), params.get("page", 1), params["limit"],
            params.get("random", False), params.get("raw", False))


    @staticmethod
    def info_from_file(path):
        posts = io.load_json(path, f"Loading post info from '{path}'...")
        if not isinstance(posts, list):  # i.e. one post not wrapped in a list
            posts = [posts]
        yield from posts


    def info_auto(self, query):
        if isinstance(query, (tuple, list)):
            yield from self.search(*query)
            return
        if isinstance(query, dict):
            yield from self.search(**query)
            return
        if isinstance(query, int):
            yield from self.info_id(query)
            return
        if not isinstance(query, str):
            log.error("Unknown query type. Expected str, int, tuple or dict.")
            yield from []
            return

        regexes = {r"^[a-fA-F\d]{32}$":                 self.info_md5,
                   r"^%s/posts/(\d+)\?*.*$" % self.url: self.info_post_url,
                   r"^%s"                   % self.url: self.info_search_url}

        for regex, function in regexes.items():
            if re.match(regex, query):
                yield from function(query)
                return

        if os.path.isfile(query):
            yield from self.info_from_file(query)
            return

        yield from self.search(query)

    # Others:

    def count_posts(self, tags=None):
        response = self.api("count_posts", tags)
        if response != []:
            return response["counts"]["posts"]
        return None

    def json_dict(self):
        return {"name": self.name, "url": self.url}


def _format_url_params(param_dict):
    new = {}
    for k, v in param_dict.items():
        # Filter out "random" and "raw" parameters if their value is False
        # because Danbooru will see them as true (bug on their side?).
        if not (k in ("random", "raw") and v is False):
            # Lowercase booleans:
            new[k] = "true" if v is True else "false" if v is False else v
    return new


# For use by modules when user doesn't specify his own.
DEFAULT = Danbooru("safebooru")
