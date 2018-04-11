"""Get notes from booru posts"""

from . import CLIENT, errors, reqwrap


def notes(post):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    try:
        return reqwrap.pybooru_api(CLIENT.note_list, None, post["id"])
    except KeyError as err:
        raise errors.CriticalKeyError(post, err.args[0], "cannot get notes")


def has_notes(post):
    return True if post.get("last_noted_at") else False
