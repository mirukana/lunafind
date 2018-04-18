"""Get notes from booru posts"""

import logging

from . import CLIENT, reqwrap


def notes(post, only_active=True):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    # last_noted_at can not exist, or be null/false in the JSON.
    if not post.get("last_noted_at"):
        # Avoid useless request.
        return []

    logging.info("Retrieving notes for post %s", post.get("id", "without ID"))

    notes_ = reqwrap.pybooru_api(CLIENT.note_list, post_id=post["id"])

    return [n for n in notes_ if n["is_active"]] if only_active else notes_
