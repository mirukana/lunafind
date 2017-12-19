#!/usr/bin/env python3
import re
from pprint import pprint
import argparse
import json
from urllib.parse import urlparse, parse_qs
from pybooru import Danbooru
import pybooru.resources
import pybooru_ext
import utils


def parse_args(args=None):
    """Define argument parser and return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
            description="Output post informations from a booru's API.",
            add_help=False,
            formatter_class=utils.CapitalisedHelpFormatter
    )

    parser._positionals.title = "Positional arguments"
    parser.add_argument(
            "query",
            action="append", nargs="+", metavar="QUERY",
            help="Tag search, post ID, post URL, search results URL or " +
                 " '%%' for the home page."
    )

    searchOpts = parser.add_argument_group("Search queries options")
    searchOpts.add_argument(
            "-p", "--pages",
            type=int, nargs="+", default=1,
            help="Pages to fetch (default: %(default)d)"
    )
    searchOpts.add_argument(
            "-l", "--limit",
            type=int, default=limit_max,
            help="Number of posts per page (default: %(default)d)"
    )
    searchOpts.add_argument(
            "-r", "--random",
            action="store_true",
            help="Request random posts from the booru."
    )
    searchOpts.add_argument(
            "-R", "--raw",
            action="store_true",
            help="Ask the booru to parse QUERY as a single literal tag."
    )

    parser._optionals.title = "General options"
    parser.add_argument(
            "-j", "--json",
            action="store_true",
            help="Output post informations as JSON."
    )
    parser.add_argument(
            "-P", "--pretty-print",
            action="store_true",
            help="Print the post infos in a human-readable way."
    )
    parser.add_argument(
            "-h", "--help",
            action="help", default=argparse.SUPPRESS,
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


def search(tags="", pages=1, limit=200, random=False, raw=False, **kwargs):
    """Return a list of dicts containing informations for every post found."""
    # Override function parameters with defined CLI arguments.
    params = {k: vars(cliArgs)[k] or k for k, v in locals().items()
              if k is not "tags" and k is not "kwargs"}

    # Query booru home page ("%" is used to have an actual QUERY CLI arg).
    if tags == "%":
        tags = None

    return client.post_list(**params)


for b in "danbooru", "safebooru":  # HTTPS for Danbooru, add safebooru
    pybooru.resources.SITE_LIST[b] = {"url": "https://%s.donmai.us" % b}

client = Danbooru("safebooru")
# TODO: migrate this to config
limit_max = 200

if __name__ == "__main__":
    cliArgs = parse_args()

    if cliArgs.pretty_print and cliArgs.json:
        print(merged_output(cliArgs.query[0], toJson=True, jsonIndent=4))
    elif cliArgs.pretty_print and not cliArgs.json:
        pprint(merged_output(cliArgs.query[0], toJson=False), indent=4)
    else:
        print(merged_output(cliArgs.query[0], toJson=cliArgs.json))
