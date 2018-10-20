# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"Misc useful functions."

import simplejson


def jsonify(dict_, **dumps_kwargs):
    kwargs = {"sort_keys": True, "ensure_ascii": False}
    kwargs.update(dumps_kwargs)
    return simplejson.dumps(dict_, **kwargs)


def bytes2human(size, prefix="", suffix=""):
    size = int(size)
    for unit in "B", "K", "M", "G", "T", "P", "E", "Z":
        if abs(size) < 1024.0:
            return f"%3.1f{prefix}{unit}{suffix}" % size
        size /= 1024.0
    return f"%.1f{prefix}Y{suffix}" % size


def simple_str_dict(dict_):
    # Returns something like   foo: "bar", lor: "em", 1: 2
    strs = [f"{k}: %s" % (f'"{v}"' if isinstance(v, str) else str(v))
            for k, v in dict_.items()]
    return ", ".join(strs)


def join_comma_and(iterable):
    if len(iterable) <= 1:
        return ", ".join(iterable)

    return "%s and %s" % (", ".join(iterable[:-1]), iterable[-1])
