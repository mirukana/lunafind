"""Misc useful functions."""

import os
import sys

import simplejson


def jsonify(obj, **dumps_kwargs):
    kwargs = {"sort_keys": True, "ensure_ascii": False}
    kwargs.update(dumps_kwargs)
    return simplejson.dumps(obj, **kwargs)


def bytes2human(size, prefix="", suffix=""):
    size = int(size)
    for unit in "B", "K", "M", "G", "T", "P", "E", "Z":
        if abs(size) < 1024.0:
            return f"%3.1f{prefix}{unit}{suffix}" % size
        size /= 1024.0
    return f"%.1f{prefix}Y{suffix}" % size


def flatten_list(list_):
    return [item for sublist in list_ for item in sublist]


def simple_str_dict(dict_):
    # Returns something like   foo: "bar", lor: "em", 1: 2
    strs = [f"{k}: %s" % (f'"{v}"' if isinstance(v, str) else str(v))
            for k, v in dict_.items()]
    return ", ".join(strs)


# next(dict_find(...)) to get all occurences, list(dict_find(...)) for all.
def dict_find(dict_, keys=(), values=(), types=(), path=None):
    """Yield path for all occurences of a key/val/type in dict, recursive."""
    path = path or []

    for k, v in dict_.items():
        if k in keys or v in values or isinstance(v, types):
            yield path + [k, v]

        if isinstance(v, dict):
            for found in dict_find(v, keys, values, types, path + [k]):
                yield found


# Remove the last value from dict_find() when passing it as key_path,
# e.g. dict_path_set(d, next(dict_find(...)[:-1], new_val)
# https://stackoverflow.com/a/13688108
def dict_path_set(dict_, key_path, value):
    """Set the value for a nested list of keys for a dict, return it."""
    try:
        for key in key_path[:-1]:
            dict_ = dict_ or {}
            dict_ = dict_.setdefault(key)
        dict_[key_path[-1]] = value
    except TypeError:  # Previous setdefault returned None:
        raise KeyError(f"{key_path[:-1]} doesn't exist in passed dict.")


def expand_path(path):
    if path is False:
        return path
    return os.path.expandvars(os.path.expanduser(path))


def blank_line():
    print(file=sys.stderr)
