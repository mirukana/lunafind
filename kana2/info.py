"""Get post information."""

import re
from urllib.parse import parse_qs, urlparse

from . import CLIENT, net, utils


def from_search(tags=None, page=1, limit=200, random=False, raw=False,
                client=CLIENT, **_):
    # pylint: disable=unused-argument
    # No md5 param because it won't return a proper list, use tags="md5:...".
    yield from net.booru_api(client.post_list, **locals())


def from_id(id_, client=CLIENT):
    yield from from_search(tags=f"id:{id_}", client=client)


def from_md5(md5, client=CLIENT):
    yield from from_search(tags=f"md5:{md5}", client=client)


def from_post_url(url, client=CLIENT):
    id_ = re.search(r"/posts/(\d+)\??.*$", url).group(1)
    yield from from_id(id_, client=client)


def from_search_url(url, client=CLIENT):
    search          = parse_qs(urlparse(url).query)
    search["limit"] = int(search.get("limit")[0]) or 20
    yield from from_search(
        search.get("tags"), search.get("page", 1), search.get("limit", 20),
        search.get("random", False), search.get("raw", False), client=client)


def from_file(path):
    yield from utils.load_json(path)
