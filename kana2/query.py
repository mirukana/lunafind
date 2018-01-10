import re
from urllib.parse import parse_qsl, urlparse

import pybooru

from . import utils

CLIENT = pybooru.danbooru.Danbooru("safebooru")
"""pybooru.danbooru.Danbooru: See :class:`~pybooru.danbooru.Danbooru`"""

def auto(*args):
    results = []

    for query in args:
        if isinstance(query, dict):
            results.extend(search(query))
            continue

        query = str(query)

        if re.match(r"^[a-fA-F\d]{32}$", query):  # 32 chars alphanumeric
            results.extend(md5(query))

        elif query.isdigit():
            results.extend(post_id(query))

        elif re.match(r"^%s/posts/(\d+)\?*.*$" % CLIENT.site_url, query):
            results.extend(url_post(query))

        elif query.startswith(CLIENT.site_url):
            results.extend(url_result(query))

        else:
            results.extend(search({"tags": query}))

    return utils.filter_duplicate_dicts(results)


def post_id(*args):
    return [{"type": "post_id", "tags": "id:%s" % post_id} for post_id in args]


def md5(*args):
    return [{"type": "md5", "tags": "md5:%s" % md5} for md5 in args]


def url_post(*args):
    return post_id(*[re.search(r"(\d+)\??.*$", url).group(1) for url in args])


def url_result(*args):
    return [dict(parse_qsl(urlparse(url).query) + [("type", "url_result")])
            for url in args]


def search(*args):
    for search_ in args:
        search_["type"] = "search"
    return list(args)
