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
                       See :func:`info.generate_page_set` for details.
    - `limit` (`int`): How many posts per page to retrieve.
    - `random` (`bool`): Randomize search results.
    - `raw` (`bool`): Parse `tags` as a single literal tag.
"""

import math
import re
from urllib.parse import parse_qsl, urlparse

from . import CLIENT, utils, tools

def auto(*args):
    """Automatically call appropriate functions to return queries.

    Args:
        *args: A post ID, MD5 hash, post URL, search result URL, tag search or
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
            If the `"page"` value is a `int` or `str`, it will be wrapped
            into a list as expected for queries.

    Returns:
        list: Query dictionaries for each argument passed.

    Examples:
        >>> query.search({"tags": "touhou", "page": [1, 2], "random": True})
        [{'tags': 'touhou', 'page': [1, 2], 'random': True, 'type': 'search'}]
    """

    for search_ in args:
        search_["type"] = "search"

        if not "page" in search_:
            search_["page"] = [1]

        if isinstance(search_["page"], (int, str)):
            search_["page"] = [search_["page"]]

    return list(args)


def get_single_page_queries(queries):
    """Return booru post information for query results.

    Takes the output of a :mod:`kana2.query` function, such as
    :func:`query.auto`.
    Appropriate calls to the booru's API will be made to retrieve information
    on the wanted posts.

    Args:
        queries (list): List of queries from :mod:`kana2.query` to process.

    Returns:
        list: Dictionaries for every post's information returned by the booru.

    Examples:
        >>> info.info(query.auto(1667182))
        [{'id': 1667182,...18bc138af5cd5bb1c50d9201d94ec8a7.jpg'}]

        >>> info.info([{"type": "search", "tags": "satsuki_rin", "limit": 1}])
        [{'id':...}]
    """

    for query in queries:
        # Default parameters, get overwritten by any query params.
        params = {"tags":   "",    "page": [1],  "limit": 200,
                  "random": False, "raw":  False}
        params.update(query)

        post_total = tools.count_posts(params["tags"])
        page_set   = generate_page_set(params["page"], post_total,
                                       params["limit"])
        total_pages  = len(page_set)
        posts_to_get = min(len(page_set) * params["limit"], post_total)

        for page in page_set:
            # Cannot just keep changing params["page"], else the same dict
            # is yielded every time (copy vs memory reference?).
            subquery                 = dict(params)
            subquery["page"]         = page
            subquery["total_pages"]  = total_pages
            subquery["posts_to_get"] = posts_to_get
            yield subquery


def generate_page_set(page_exprs, total_posts=None, limit=None):
    """Return a set of valid booru pages from a list of expressions.

    An expression can be a:
    - Single page (e.g. `"1"`);
    - Range (`"3-5"`);
    - Range from the first page to a given page (`"+6"`);
    - Range from the a given page to the last page (`"1+"`).

    Args:
        page_exprs (list): Page expressions to parse.
        total_posts (int, optional): Total number of posts for the tag search
            pages are generated for.  Needed for `"<page>+"` expressions.
            Defaults to `None`.
        limit (int, optional): Number of posts per page.
            Needed for `"<page>+"` expressions.  Defaults to `None`.

    Raises:
        TypeError: If a `"<page>+"` item is present in `pages`, but
                   the `limit` or `total_posts` parameter isn't set.

    Examples:
        >>> tools.generate_page_set(["20", "7", "6-9", "+3"])
        {1, 2, 3, 6, 7, 8, 9, 20}

        >>> tools.generate_page_set(["1+"])
        ...
        TypeError: limit and total_posts parameters required to use the
...                <page>+ feature.

        >>> tools.generate_page_set(["1+"], tools.count_posts("ib"), 200)
        {1, 2, 3, 4, 5, 6}
    """

    page_set = set()

    for page in page_exprs:
        page = str(page)

        if page.isdigit():
            page_set.add(int(page))
            continue

        # e.g. -p 3-10: All the pages in the range (3, 4, 5...).
        if re.match(r"^\d+-\d+$", page):
            begin = int(page.split("-")[0])
            end = int(page.split("-")[-1])

        # e.g. -p 2+: All the pages in a range from 2 to the last possible.
        elif re.match(r"^\d+\+$", page):
            begin = int(page.split("+")[0])

            if not limit or not total_posts:
                raise TypeError("limit and total_posts parameters required "
                                "to use the <page>+ feature.")

            end = math.ceil(total_posts / limit)

        # e.g. -p +5: All the pages in a range from 1 to 5.
        elif re.match(r"^\+\d+$", page):
            begin = 1
            end = int(page.split("+")[-1])

        else:
            raise ValueError("Invalid page expression: '%s'" % page)

        page_set.update(range(begin, end + 1))

    return page_set
