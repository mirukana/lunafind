"""Generate query dictionaries to be used with other kana2 modules.

Query dictionaries can include the following keys:
    - `type` (`str`): The kind of query, can be:
        - `"post_id"`
        - `"md5"`
        - `"url_post"`
        - `"url_result"`
        - `"search"`
    - `tags` (`str`): The tags to search for.
        Can be any tag combination that works on the booru.
        Note, Danbooru limits searches to 2 tags for normal members/visitors.
    - `page` (`list`): List of pages to search.
                       See :func:`tools.generate_page_set` for details.
    - `limit` (`int`): How many posts per page to retrieve.
    - `random` (`bool`): Randomize search results.
    - `raw` (`bool`): Parse `tags` as a single literal tag.
"""

import re
from urllib.parse import parse_qsl, urlparse

import pybooru

from . import utils

CLIENT = pybooru.danbooru.Danbooru("safebooru")
"""pybooru.danbooru.Danbooru: See :class:`~pybooru.danbooru.Danbooru`"""

def auto(*args):
    """Automatically call appropriate functions to return queries.

    Args:
        *args: A post ID, MD5 hash, post URL, search result URL or
               tag search parameters dictionary.

    Returns:
        list: Query dictionaries for each argument passed.
              Duplicate queries are discarded.

    Examples:
        >>> query.auto(1, 1, 2, "ca0339e7b4c9648db71b79b1df37158e",
                      "https://safebooru.donmai.us/posts/2935330",
                      "https://safebooru.donmai.us/posts.json?tags=shinki",
                      {"tags":"mima", "page":["+4", 10]})
        [{'tags': 'id:2935330', 'type': 'url_post'},
...      {'tags': 'shinki', 'type': 'url_result'},
...      {'page': ['+4', 10], 'tags': 'mima', 'type': 'search'},
...      {'tags': 'id:1', 'type': 'post_id'},
...      {'tags': 'md5:ca0339e7b4c9648db71b79b1df37158e', 'type': 'md5'},
...      {'tags': 'id:2', 'type': 'post_id'}]
    """
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
    """Return queries to find single posts by ID.

    Args:
        *args (str): A number corresponding to a post's ID.
                     `int` arguments are automatically converted.

    Returns:
        list: Query dictionaries for each argument passed.

    Examples:
        >>> query.post_id(2903102, 2865291)
        [{'type': 'post_id', 'tags': 'id:2903102'},
...      {'type': 'post_id', 'tags': 'id:2865291'}]
    """
    return [{"type": "post_id", "tags": "id:%s" % post_id} for post_id in args]


def md5(*args):
    """Return queries to find single posts by MD5 hash.

    Args:
        *args (str): A post's MD5 hash.

    Returns:
        list: Query dictionaries for each argument passed.

    Examples:
        >>> query.md5("0a8ef2bf611bdf59045730a4710bd31a")
        [{'type': 'md5', 'tags': 'md5:0a8ef2bf611bdf59045730a4710bd31a'}]
    """

    return [{"type": "md5", "tags": "md5:%s" % md5} for md5 in args]


def url_post(*args):
    """Return queries to find single posts by URL.

    Args:
        *args (str): A post URL.

    Returns:
        list: Query dictionaries for each argument passed.

    Examples:
        >>> query.post_id("https://safebooru.donmai.us/posts/1092827")
        [{'type': 'url_post', 'tags': 'id:1092827'}]
    """

    return [{"type": "url_post", "tags": "id:%s" % \
             re.search(r"(\d+)\??.*$", url).group(1)} for url in args]


def url_result(*args):
    """Return queries to find posts by search results URL.

    Args:
        *args (str): A search result URL.

    Returns:
        list: Query dictionaries for each argument passed.

    Examples:
        >>> url = "https://safebooru.donmai.us/posts?tags=scenery&page=3"
        >>> query.url_result(url)
        [{'type': 'url_result', 'tags': 'scenery', 'page': '3'}]
    """

    return [dict([("type", "url_result")] + parse_qsl(urlparse(url).query))
            for url in args]


def search(*args):
    """Return queries to find posts by tag search.

    Args:
        *args (str): A dictionary of search parameters.
                     Possible parameters are any key found in query
                     directionaries, minus `type`.

    Returns:
        list: Query dictionaries for each argument passed.

    Examples:
        >>> query.search({"tags": "touhou", "page": [1, 2], "random": True})
        [{'tags': 'touhou', 'page': [1, 2], 'random': True, 'type': 'search'}]
    """

    for search_ in args:
        search_["type"] = "search"
    return list(args)
