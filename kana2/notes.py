"""Get notes from booru posts"""

from . import CLIENT, errors, reqwrap


def notes(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    return reqwrap.pybooru_api(CLIENT.note_list, None, post["id"])


def has_notes(post):
    # last_noted_at can not exist, or be null/false in the JSON.
    return True if post.get("last_noted_at") else False
