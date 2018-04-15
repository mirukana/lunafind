"""Get artist commentary(ies) from booru posts"""

import requests

from . import CLIENT, errors, reqwrap


def artcom(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    try:
        return CLIENT.artist_commentary_list(None, post["id"])
    except KeyError as err:
        raise errors.CriticalKeyError(post, err.args[0], "cannot get artcom")


def has_artcom(post):
    return True if post.get("last_commented_at") else False
