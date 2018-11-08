# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

"Misc useful functions."

import re
import sys
from typing import Union

import pendulum as pend
import simplejson

# pylint: disable=no-name-in-module
from fastnumbers import fast_float, fast_int

from . import TERM

SIZE_UNITS = "BKMGTPEZY"

def bytes2human(size: Union[int, float], prefix: str = "", suffix: str = ""
               ) -> str:
    size = fast_float(size)  # Prevent proxied size problems with round()
    unit = ""

    for unit in SIZE_UNITS:
        if size < 1024:
            break

        size /= 1024

    size = fast_int(size)    if unit in "BK" else \
           round(size, 1) if unit == "M" else \
           round(size, 2)

    return f"{size}{prefix}{unit}{suffix}"


def human2bytes(size: Union[int, float, str]) -> float:
    size   = str(size)
    result = fast_float(size.rstrip("%s%s" % (SIZE_UNITS, SIZE_UNITS.lower())))

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
        return fast_int(w) / fast_int(h)

    return fast_float(value)


AGE_UNIT_TO_SUBTRACT_ARG = {
    ("Y", "y", "year"):                 "years",
    ("M", "mo", "month"):               "months",
    ("w", "week"):                      "weeks",
    ("d", "day"):                       "days",
    ("h", "hour"):                      "hours",
    ("m", "mi", "mn", "min", "minute"): "minutes",
    ("s", "sec", "second"):             "seconds",
    ("ms", "microsec", "microsecond"):  "microseconds"
}

def age2date(age: str) -> pend.DateTime:
    try:
        return pend.parse(age)  # If this is already a normal date
    except pend.parsing.exceptions.ParserError:
        pass

    user_unit  = age.lstrip("0123456789.")
    value      = abs(fast_float(age.replace(user_unit, "")))
    found_unit = None

    for units, shift_unit in AGE_UNIT_TO_SUBTRACT_ARG.items():
        for unit in units:
            if user_unit in (unit, f"{unit}s"):
                found_unit = shift_unit

    if not found_unit:
        raise ValueError(f"Invalid age unit: {user_unit!r}")

    return pend.now().subtract(**{found_unit: value})


JSONIFY_DEFAULT_PARAMS = {"sort_keys": True, "ensure_ascii": False}

def jsonify(dict_: dict, **dumps_kwargs) -> str:
    kwargs = {**JSONIFY_DEFAULT_PARAMS, **dumps_kwargs}
    return simplejson.dumps(dict_, **kwargs)


def join_comma_and(*strings: str) -> str:
    if len(strings) <= 1:
        return ", ".join(strings)

    return "%s and %s" % (", ".join(strings[:-1]), strings[-1])


def print_colored_help(doc: str, exit_code: int = 0) -> None:
    doc = doc.splitlines()

    # Usage:
    doc[0] = re.sub(r"(Usage: +)",
                    f"%s{TERM.blue}" % TERM.magenta_bold(r"\1"), doc[0])
    # [things]
    doc[0] = re.sub(r"\[(\S+)\]",
                    f"[%s{TERM.blue}]" % TERM.bold(rf"\1"), doc[0])

    doc[0] = f"{doc[0]}{TERM.normal}"
    doc    = "\n".join(doc)

    styles = {
        r"`(.+?)`":      "green",         # `things`
        r"^(\S.+:)$":    "magenta_bold",  #  Sections:
        r"^(  [A-Z]+)$": "blue_bold",     #  ARGUMENT
        r"^(  \S.+)$":   "blue",          #  Two-space indented lines
        r"^(\s*-)":      "magenta",       #  - Dash lists
    }

    for reg, style in styles.items():
        doc = re.sub(reg, getattr(TERM, style)(r"\1"), doc, flags=re.MULTILINE)

    doc = re.sub(r"(-{1,2}[a-zA-Z\d]+ +)([A-Z]+)",
                 r"\1%s%s%s" % (TERM.blue_bold(r"\2"), TERM.normal, TERM.blue),
                 doc)

    print(doc)
    sys.exit(exit_code)
