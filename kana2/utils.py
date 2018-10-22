# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"Misc useful functions."

from typing import Union

import simplejson

SIZE_UNITS = "BKMGTPEZY"


def bytes2human(size: Union[int, float], prefix: str = "", suffix: str = ""
               ) -> str:
    unit = ""

    for unit in SIZE_UNITS:
        if size < 1024:
            break

        size /= 1024

    size = int(size) if str(size).endswith(".0") else round(size, 2)
    return f"{size}{prefix}{unit}{suffix}"


def human2bytes(size: Union[int, float, str]) -> float:
    size   = str(size)
    result = float(size.rstrip("%s%s" % (SIZE_UNITS, SIZE_UNITS.lower())))

    if size.lstrip(f"0123456789.").upper() in ("", "B", "O"):
        return result

    for unit in SIZE_UNITS.lstrip("B"):
        result *= 1024
        if size.rstrip("iIoObB")[-1].upper() == unit:
            break

    return result


def ratio2float(value: Union[int, float, str]) -> float:
    if isinstance(value, str) and ":" in value:
        w, h = value.split(":")
        return int(w) / int(h)

    return float(value)


def jsonify(dict_: dict, **dumps_kwargs) -> str:
    kwargs = {"sort_keys": True, "ensure_ascii": False}
    kwargs.update(dumps_kwargs)
    return simplejson.dumps(dict_, **kwargs)


def simple_str_dict(dict_: dict) -> str:
    # Returns something like   foo: "bar", lor: "em", 1: 2
    strs = [f"{k}: %s" % (f'"{v}"' if isinstance(v, str) else str(v))
            for k, v in dict_.items()]
    return ", ".join(strs)


def join_comma_and(*strings: str) -> str:
    if len(strings) <= 1:
        return ", ".join(strings)

    return "%s and %s" % (", ".join(strings[:-1]), strings[-1])
