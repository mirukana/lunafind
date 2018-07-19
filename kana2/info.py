"""Get post information."""

import logging as log
import os
import re
from urllib.parse import parse_qs, urlparse

from . import config, net, io, utils


def from_search(tags="", page=1, limit=200, random=False, raw=False,
                client=config.CLIENT):
    # pylint: disable=unused-argument
    if re.match(r"^(id|md5):[a-fA-F\d]+$", tags):
        params = {"tags": tags}
    else:
        params = {k: v for k, v in locals().items() if k != "client" and v}

    log.info("Retrieving post info - %s", utils.simple_str_dict(params))
    yield from net.booru_api(client.post_list, **params)


def from_id(id_, client=config.CLIENT):
    yield from from_search(tags=f"id:{id_}", client=client)


def from_md5(md5, client=config.CLIENT):
    yield from from_search(tags=f"md5:{md5}", client=client)


def from_post_url(url, client=config.CLIENT):
    id_ = re.search(r"/posts/(\d+)\??.*$", url).group(1)
    yield from from_id(id_, client=client)


def from_search_url(url, client=config.CLIENT):
    search          = parse_qs(urlparse(url).query)
    search["limit"] = int(search.get("limit")[0]) or 20
    yield from from_search(
        search.get("tags"), search.get("page", 1), search.get("limit", 20),
        search.get("random", False), search.get("raw", False), client=client)


def from_file(path):
    posts = io.load_json(path, f"Loading post info from '{path}'...")
    if not isinstance(posts, list):  # i.e. one post not wrapped in a list
        posts = [posts]
    yield from posts


def from_auto(query):
    if isinstance(query, (tuple, list)):
        yield from from_search(*query)
        return

    if isinstance(query, dict):
        yield from from_search(**query)
        return

    if isinstance(query, int):
        yield from from_id(query)
        return

    if not isinstance(query, str):
        log.error("Unknown query type. Expected str, int, tuple or dict.")
        yield from []
        return

    regexes = {
        r"^[a-fA-F\d]{32}$":                               from_md5,
        r"^%s/posts/(\d+)\?*.*$" % config.CLIENT.site_url: from_post_url,
        r"^%s"                   % config.CLIENT.site_url: from_search_url
    }

    for regex, function in regexes.items():
        if re.match(regex, query):
            yield from function(query)
            return

    if os.path.isfile(query):
        yield from from_file(query)
        return

    yield from from_search(query)
