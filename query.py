#!/usr/bin/env python3
import sys
import re
import pprint
from urllib.parse import urlparse, parse_qs
from pybooru import Danbooru
import pybooru.resources
import utils


def merged_list(*args):
    """Call auto() for every arguments, return a flattened list of results."""
    results = []
    for arg in args:
        results += auto(arg)
    return utils.filter_duplicate_dicts(results)


def auto(arg):
    """
    Detect what kind of query an argument is,
    return a list of post dicts from the appropriate function.
    """
    if re.match(r"^[a-fA-F\d]{32}$", str(arg)):  # 32 chars alphanumeric
        return md5(arg)

    if arg.isdigit():
        return _id(arg)

    if re.match(r"^%s/posts/(\d+)\?*.*$" % client.site_url, str(arg)):
        return url_post(arg)

    if str(arg).startswith(client.site_url):
        return url_result(arg)

    return search(arg)


def url_post(url):
    """Call _id() with the post number in the URL."""
    return _id(re.search(r"(\d+)\?*.*$", url).group(1))


def _id(_id):
    """Return one dict in a list for the found post on the booru."""
    return client.post_list(tags="id:%s" % _id)


def url_result(url):
    """Call search() with the parameters found in the URL."""
    return search(**parse_qs(urlparse(url).query))


def md5(md5):
    """Call search() to find a post with a MD5 hash."""
    return client.post_list(tags="md5:%s" % md5)


def search(tags="", page=1, limit=200, random=False, raw=False, **kwargs):
    """Return a list of dicts containing informations for every post found."""
    return client.post_list(**locals())


for b in "danbooru", "safebooru":  # HTTPS for Danbooru, add safebooru
    pybooru.resources.SITE_LIST[b] = {"url": "https://%s.donmai.us" % b}

client = Danbooru("safebooru")

if __name__ == "__main__":
    # Filter out duplicate args to avoid useless requests and [0] (script path)
    queries = set(sys.argv[1:])
    pprint.pprint(merged_list(*queries))
