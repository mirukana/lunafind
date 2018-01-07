import json
import math
import re
import sys
import urllib.parse

from colored import attr, fg
from halo import Halo

from . import args
from . import client
from . import tools

# TODO: migrate those to config
colors = {
    "info": "green",
    "info2": "blue"
}


def merged_output(queries, toJson=False, jsonIndent=None):
    """Call auto() for every arguments, return a flattened list of results."""
    results = []
    for query in queries:
        results += auto(query)

    results = tools.filter_duplicates(results)
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
    spinner = Halo(
            text="Querying post %s%s%s" % (fg(colors["info"]), _id, attr(0)),
            spinner="arrow", stream=sys.stderr, color="yellow")
    spinner.start()

    result = tools.exec_pybooru_call(client.post_list, tags="id:%s" % _id)

    spinner.succeed("Fetched post %s%s%s" % (fg(colors["info"]), _id, attr(0)))
    return result


def url_result(url):
    """Call search() with the parameters found in the URL."""
    return search(**urllib.parse.parse_qs(urllib.parse.urlparse(url).query))


def md5(md5):
    """Call search() to find a post with a MD5 hash."""
    spinner = Halo(
            text="Querying MD5 %s%s%s" % (fg(colors["info"]), md5, attr(0)),
            spinner="arrow", stream=sys.stderr, color="yellow")
    spinner.start()

    result = tools.exec_pybooru_call(client.post_list, tags="md5:%s" % md5)

    spinner.succeed("Fetched MD5 %s%s%s" % (fg(colors["info"]), md5, attr(0)))
    return result


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
            params[param] = args.parsed.__dict__[param]
        except (AttributeError, KeyError):
            pass

    if type(params["page"]) != list:
        params["page"] = [params["page"]]

    # Generate full list of pages as integers without duplicates.
    page_set = set()
    post_total = tools.count_posts(params["tags"])

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
            end = math.ceil(post_total / params["limit"])

        # e.g. -p +5: All the pages in a range from 1 to 5.
        elif re.match(r"^\+\d+$", str(page)):
            begin = 1
            end = int(page.split("+")[-1])

        page_set.update(range(begin, end + 1))

    posts_to_get = min(len(page_set) * params["limit"], post_total)
    page_nbr = str(len(page_set))
    page_nbr += " pages" if len(page_set) > 1 else " page"

    spinner = Halo(spinner="arrow", stream=sys.stderr, color="yellow")
    spinner.start()

    results = []
    for page in page_set:
        spinner.text = ("Querying search {0}{3}{2}, page {1}{4}{2} "
                        "({0}{5}{2} posts over {0}{6}{2})").format(
                fg(colors["info"]), fg(colors["info2"]), attr(0),
                params["tags"], page, posts_to_get, page_nbr)

        params["page"] = page
        results += tools.exec_pybooru_call(client.post_list, **params)

    spinner.succeed(
            "Fetched search {0}{2}{1} ({0}{3}{1} posts over {0}{4}{1})".format(
                fg(colors["info"]), attr(0),
                params["tags"], posts_to_get, page_nbr))

    return results
