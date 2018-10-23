# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"Misc useful functions."

from typing import Union

import arrow
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


AGE_TO_ARROW_SHIFT_ARG = {
    ("Y", "y", "year"):                 "years",
    ("M", "mo", "month"):               "months",
    ("w", "week"):                       "weeks",
    ("d", "day"):                       "days",
    ("h", "hour"):                      "hours",
    ("m", "mi", "mn", "min", "minute"): "minutes",
    ("s", "sec", "second"):             "seconds",
    ("ms", "microsec", "microsecond"):  "microseconds"
}

def age2date(age: str) -> arrow.Arrow:
    try:
        return arrow.get(age)  # If this is already a normal date
    except arrow.parser.ParserError:
        pass

    user_unit  = age.lstrip("0123456789.")
    value      = -abs(float(age.replace(user_unit, "")))
    found_unit = None

    for units, shift_unit in AGE_TO_ARROW_SHIFT_ARG.items():
        for unit in units:
            if user_unit in (unit, f"{unit}s"):
                found_unit = shift_unit

    if not found_unit:
        raise ValueError(f"Invalid age unit: {user_unit!r}")

    return arrow.now().shift(**{found_unit: value}).to("UTC-4")


JSONIFY_DEFAULT_PARAMS = {"sort_keys": True, "ensure_ascii": False}

def jsonify(dict_: dict, **dumps_kwargs) -> str:
    kwargs = {**JSONIFY_DEFAULT_PARAMS, **dumps_kwargs}
    return simplejson.dumps(dict_, **kwargs)


def join_comma_and(*strings: str) -> str:
    if len(strings) <= 1:
        return ", ".join(strings)

    return "%s and %s" % (", ".join(strings[:-1]), strings[-1])
