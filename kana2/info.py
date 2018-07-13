"""Get post information"""

import logging
from . import CLIENT, net


def for_id(*booru_ids, client=CLIENT):
    for bid in booru_ids:
        logging.info(f"Retrieving info for post {bid}...")
        yield net.booru_api(client.post_show, bid)
