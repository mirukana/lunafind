"""Get notes from booru posts"""

from . import CLIENT, reqwrap


def has_notes(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    # last_noted_at can not exist, or be null/false in the JSON.
    return True if post.get("last_noted_at") else False


def notes(post, only_active=True):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    notes_ = reqwrap.pybooru_api(CLIENT.note_list, post_id=post["id"])

    return [n for n in notes_ if n["is_active"]] if only_active else notes_
