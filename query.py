#!/usr/bin/env python3
import re
from pprint import pprint
import argparse
import json
from urllib.parse import urlparse, parse_qs
from math import ceil
from pybooru import Danbooru
import pybooru.resources
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
            "-p", "--page",
            nargs="+", default=1,
            help="Pages to fetch (default: %(default)d)\n" +
                 "Can be a single page or a range (e.g. 3-777, 1+ or +20)"
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
    # Sort posts from newest to oldest, like a booru's results would show.
    results = sorted(results, key=lambda post: post["id"], reverse=True)

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

    return search(tags=query)


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

    # Leave out False/empty keys; because if for example "random=False" is
    # passed to Danbooru, it will behave like "random=true".
    # Also leave out tags=%, no tags parameter means fetch the home page.
    # % is used to have an actual QUERY CLI arg).
    params = {k: v for k, v in locals().items() if v and v != "%"}

    # Try to override function parameters with defined CLI arguments.
    for param, _ in params.items():
        try:
            params[param] = vars(cliArgs)[param]
        except (AttributeError, KeyError):
            pass

    if type(params["page"]) != list:
        params["page"] = [params["page"]]

    # Generate full list of pages as integers without duplicates.
    page_set = set()

    for page in params["page"]:
        if str(page).isdigit():
            page_set.add(int(page))
            continue

        # e.g. -p 3-10: All the pages in the range (3, 4, 5...).
        if re.match(r"^\d+-\d+$", str(page)):
            begin = int(page.split("-")[0])
            end = int(page.split("-")[-1])

        # e.g. -p 2+: All the pages in a range from 2 to the last possible.
        elif re.match(r"^\d+\+$", str(page)):
            begin = int(page.split("+")[0])
            end = ceil(count_posts(params["tags"]) / params["limit"])

        # e.g. -p +5: All the pages in a range from 1 to 5.
        elif re.match(r"^\+\d+$", str(page)):
            begin = 1
            end = int(page.split("+")[-1])

        page_set.update(range(begin, end + 1))

    results = []
    for page in page_set:
        params["page"] = page
        results += client.post_list(**params)
    return results


def count_posts(tags=None):
    return client.count_posts(tags)["counts"]["posts"]


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
