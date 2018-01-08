import re
from urllib.parse import urlparse, parse_qsl

import pybooru

from . import utils

# TODO: Make this work with any booru URL
client = pybooru.Danbooru("safebooru")


def auto(*args):
    results = []

    for query in args:
        if type(query) is dict:
            results += search(query)
            continue

        query = str(query)

        if re.match(r"^[a-fA-F\d]{32}$", query):  # 32 chars alphanumeric
            results += md5(query)

        elif query.isdigit():
            results += post_id(query)

        elif re.match(r"^%s/posts/(\d+)\?*.*$" % client.site_url, query):
            results += url_post(query)

        elif query.startswith(client.site_url):
            results += url_result(query)

        else:
            results += search({"tags": query})

    return utils.filter_duplicate_dicts(results)


def post_id(*args):
    return [{"tags": "id:%s" % post_id} for post_id in args]


def md5(*args):
    return [{"tags": "md5:%s" % md5} for md5 in args]


def url_post(*args):
    return post_id(*[re.search(r"(\d+)\??.*$", url).group(1) for url in args])


def url_result(*args):
    return [dict(parse_qsl(urlparse(url).query, True)) for url in args]


def search(*args):
    return list(args)
