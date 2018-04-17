"""Get artist commentary(ies) from booru posts"""

from . import CLIENT, reqwrap


def has_artcom(post):
    return True if post.get("last_commented_at") else False


def artcom(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    return reqwrap.pybooru_api(CLIENT.artist_commentary_list,
                               post_id=post["id"])
