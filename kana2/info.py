"""Get booru post information from a query."""

import sys

import pybooru
from halo import Halo

from . import tools

CLIENT = pybooru.danbooru.Danbooru("safebooru")
"""pybooru.danbooru.Danbooru: See :class:`~pybooru.danbooru.Danbooru`"""

def info(queries):
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
    results = []

    for query in queries:
        params = {"tags": "", "page": [1], "limit": 200,
                  "random": False, "raw": False}  # defaults
        params.update(query)

        post_total = tools.count_posts(params["tags"])
        page_set   = tools.generate_page_set(params["page"], params["limit"],
                                             post_total)
        page_nbr = len(page_set)
        posts_to_get = min(len(page_set) * params["limit"], post_total)

        spinner = Halo(spinner="arrow", stream=sys.stderr, color="yellow")
        spinner.start()

        for page in page_set:
            spinner.text = get_spinner_text("running", query, posts_to_get,
                                            page_nbr)

            params["page"] = page
            results.extend(tools.exec_pybooru_call(CLIENT.post_list, **params))

        spinner.succeed(get_spinner_text("success", query, posts_to_get,
                                         page_nbr))

    return results


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
