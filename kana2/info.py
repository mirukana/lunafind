"""Get booru post information from a query dictionary."""

import logging
import math
# import multiprocessing
import re

from . import CLIENT, tools

# TODO: Update docstrings

def info(queries):
    for subquery in get_subqueries(queries):
        logging.info(
            "Getting infos - tags: %s, page: %s, total: %s, "
            "posts: %s, limit: %s%s%s",
            subquery["tags"], subquery["page"], subquery["total_pages"],
            subquery["posts_to_get"], subquery["limit"],
            ", random" if subquery["random"] else "",
            ", raw"    if subquery["raw"]    else "")

        for post in tools.exec_pybooru_call(CLIENT.post_list, **subquery):
            yield post


def get_subqueries(queries):
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



def get_spinner_text(state, query, posts_to_get=None, page_nbr=None):
    """Return a suitable text for the Halo spinner when querying post info.

    Args:
        state (str): State of the spinner, modifies the first word returned.
            "running" or "success" ("Fetching...", "Fetched...").
        query (dict): A query from :mod:`kana2.query`.
        posts_to_get (int, optional): Number of total posts for the query.
            Used for `searches` or `url_result` queries.
        page_nbr (set, optional): Number of pages that will be queried.

    Returns:
        str: Text to be used for the spinner.

    Examples:
        >>> info.get_spinner_text("running", query.auto(2366601)[0])
        'Fetching info for post 2366601'

        >>> info.get_spinner_text("success", {"type": "search", \
"tags": "maribel_hearn", "page": ["1-5"]}, posts_to_get=5 * 200, page_nbr=5)
        'Fetched info for search maribel_hearn (1000 posts over 5 pages)'

        >>> info.get_spinner_text("success", {"type": "search", \
"tags": "usami_renko"}, posts_to_get=200)
        'Fetched info for search usami_renko (200 posts)'

        >>> info.get_spinner_text("success", {"type": "search", \
"tags": "hakurei_reimu", "page": ["+3"]}, page_nbr=3)
        'Fetched info for search hakurei_reimu (3 pages)'
    """

    info_state = {"running": "Fetching", "success": "Fetched"}

    if "type" not in query:
        query["type"] = "unkown"

    info_query = {
        "unknown":    "query %s"           % query["tags"],
        "md5":        "md5 %s"             % query["tags"][len("md5:"):],
        "post_id":    "post %s"            % query["tags"][len("id:"):],
        "url_post":   "post %s from URL"   % query["tags"][len("id:"):],
        "url_result": "search %s from URL" % query["tags"],
        "search":     "search %s"          % query["tags"]
    }

    info_search = posts = over = pages = ""
    if query["type"] in ("search", "url_result"):
        if posts_to_get:
            posts = "%s posts" % posts_to_get
        if posts_to_get and page_nbr:
            over = " over "
        if page_nbr:
            pages = "%s page%s" % (page_nbr, "s" if page_nbr > 1 else "")
        if posts or pages:
            info_search = " (%s%s%s)" % (posts, over, pages)

    return "%s info for %s%s" % (
        info_state[state],
        info_query[query["type"]],
        info_search
    )
