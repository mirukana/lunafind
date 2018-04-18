"""Get artist commentary from booru posts"""

import arrow

from . import CLIENT, reqwrap


def artcom(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    # If commentary/commentary_request tag in meta tags, post has an artcom.
    # This should be true unless the post was created today, in which case
    # the tagging bot may have not processed them yet.

    meta_tags = " %s " % post.get("tag_string_meta")  # Faster than regex

    if " commentary "         in meta_tags or \
       " commentary_request " in meta_tags or \
       arrow.get(post["created_at"]) >= arrow.now().shift(hours=-24):
        # Return [] if a post created today has no artcom
        return reqwrap.pybooru_api(CLIENT.artist_commentary_list,
                                   post_id=post["id"])

    return []
