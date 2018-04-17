"""Get artist commentary from booru posts"""

from . import CLIENT, reqwrap


def has_artcom(post):
    # If commentary/commentary_request tag in meta tags, post has an artcom.
    # The trick below is faster than using regex.
    meta_tags = " %s " % post.get("tag_string_meta")
    return " commentary " in meta_tags or " commentary_request " in meta_tags


def artcom(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    return reqwrap.pybooru_api(CLIENT.artist_commentary_list,
                               post_id=post["id"])
