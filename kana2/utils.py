"""Misc useful functions."""

import os
import sys

import ujson


def jsonify(obj, indent=False):
    # Serialize Arrow date object:
    if "fetch_date" in obj:
        obj["fetch_date"] = (obj["fetch_date"]
                             .format("YYYY-MM-DDTHH:mm:ss.SSSZZ"))

    dumps_kwargs = {"sort_keys": True,     "double_precision": 2,
                    "ensure_ascii": False, "escape_forward_slashes": False}
    if indent:
        dumps_kwargs["indent"] = 4

    return ujson.dumps(obj, **dumps_kwargs)


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


def expand_path(path):
    if path is False:
        return path
    return os.path.expandvars(os.path.expanduser(path))


def blank_line():
    print(file=sys.stderr)
