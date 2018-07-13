"""Get post information."""

import logging as log
from . import CLIENT, net


def for_id(*booru_ids, client=CLIENT):
    for bid in booru_ids:
        log.info(f"Retrieving info for post {bid}...")
        yield net.booru_api(client.post_show, bid)
