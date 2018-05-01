"""Get artist commentary from booru posts"""

import logging

import arrow

from . import CLIENT, reqwrap


def artcom(post, client=CLIENT):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    # If post has commentary/commentary_request tag, it should have an artcom.
    # Trick below is faster than using regex.
    meta_tags = " %s " % post.get("tag_string_meta")

    meta_comm = " commentary " in meta_tags or \
                " commentary_request " in meta_tags

    # If the post was created in the last 24 hours, the tagging bot may have
    # not processed them yet to add commentary/commentary_request tags.
    created_24h = arrow.get(post["created_at"]) >= arrow.now().shift(hours=-24)

    if meta_comm or created_24h:
        logging.info("Retrieving%s artist commentary for post %s",
                     " potential" if created_24h and not meta_comm else "",
                     post.get("id", "without ID"))

        # Will return [] if a post created in the last 24 hours has no artcom.
        return reqwrap.pybooru_api(client.artist_commentary_list,
                                   post_id=post["id"])

    return []
