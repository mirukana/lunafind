import sys
from collections import defaultdict

import pybooru
from halo import Halo

from . import tools

CLIENT = pybooru.danbooru.Danbooru("safebooru")
"""pybooru.danbooru.Danbooru: See :class:`~pybooru.danbooru.Danbooru`"""

def info(queries):
    results = []

    for query in queries:
        params = {"tags": "", "page": [1], "limit": 200,
                  "random": False, "raw": False}  # defaults
        params.update(query)

        post_total = tools.count_posts(params["tags"])
        page_set   = tools.generate_page_set(params["page"], params["limit"],
                                             post_total)
        posts_to_get = min(len(page_set) * params["limit"], post_total)

        spinner = Halo(spinner="arrow", stream=sys.stderr, color="yellow")
        spinner.start()

        for page in page_set:
            spinner.text = get_spinner_text("running", query, posts_to_get,
                                            page_set)

            params["page"] = page
            results.extend(tools.exec_pybooru_call(CLIENT.post_list, **params))

        spinner.succeed(get_spinner_text("succeed", query, posts_to_get,
                                         page_set))

    return results


def get_spinner_text(action, query, posts_to_get, page_set):
    info_action = {"running": "Fetching", "succeed": "Fetched"}

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

    info_page = defaultdict(lambda: "", {
        "search": " (%s posts over %s page%s)" % (
            posts_to_get,
            len(page_set),
            "s" if len(page_set) > 1 else ""
        )
    })
    info_page["url_result"] = info_page["search"]

    return "%s info for %s%s" % (
        info_action[action],
        info_query[query["type"]],
        info_page[query["type"]]
    )
