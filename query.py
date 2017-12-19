#!/usr/bin/env python3
import sys
import re
from pprint import pprint
import argparse
import json
from urllib.parse import urlparse, parse_qs
from pybooru import Danbooru
import pybooru.resources
import utils


def parse_args(args=None):
    parser = argparse.ArgumentParser(
            description="Fill me",
            add_help=False,
            formatter_class=utils.CapitalisedHelpFormatter
    )

    parser._positionals.title = "Positional arguments"
    parser.add_argument(
            "query",
            action="append",
            nargs="*",
            metavar="QUERY",
            help="Tag search, post ID, post URL or search results URL."
    )

    parser._optionals.title = "Optional arguments"
    parser.add_argument(
            "-j", "--json",
            action="store_true",
            help="Output post informations as JSON instead of Python dict."
    )
    parser.add_argument(
            "-P", "--pretty-print",
            action="store_true",
            help="Print the post infos in a human-readable way."
    )
    parser.add_argument(
            "-h", "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit."
    )

    # Defaults to the CLI arguments
    return parser.parse_args(args if args else None)


def merged_output(queries, toJson=False, jsonIndent=0):
    """Call auto() for every arguments, return a flattened list of results."""
    results = []
    for query in queries:
        results += auto(query)
    results = utils.filter_duplicate_dicts(results)

    if toJson:
        return json.dumps(results, ensure_ascii=False, indent=jsonIndent)

    return results


def auto(query):
    """
    Detect what kind of query an argument is,
    return a list of post dicts from the appropriate function.
    """
    if re.match(r"^[a-fA-F\d]{32}$", str(query)):  # 32 chars alphanumeric
        return md5(query)

    if query.isdigit():
        return _id(query)

    if re.match(r"^%s/posts/(\d+)\?*.*$" % client.site_url, str(query)):
        return url_post(query)

    if str(query).startswith(client.site_url):
        return url_result(query)

    return search(query)


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

if __name__ != "__main__":
    sys.exit()

cliArgs = parse_args()

if cliArgs.pretty_print and cliArgs.json:
    print(merged_output(cliArgs.query[0], toJson=True, jsonIndent=4))
elif cliArgs.pretty_print and not cliArgs.json:
    pprint(merged_output(cliArgs.query[0], toJson=False), indent=4)
else:
    print(merged_output(cliArgs.query[0], toJson=cliArgs.json))
