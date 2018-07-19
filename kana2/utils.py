"""Misc useful functions."""

import json
import os
import sys

from . import config, net


def jsonify(obj, indent=False):
    # Serialize Arrow date object:
    if "fetch_date" in obj:
        obj["fetch_date"] = (obj["fetch_date"]
                             .format("YYYY-MM-DDTHH:mm:ss.SSSZZ"))

    if not indent:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False)

    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=4)


def bytes2human(size, prefix="", suffix=""):
    """Return byte sizes as a human-readable number.

    Args:
        size (int): A size in bytes.
        prefix (str, optional): String shown before the unit. Defaults to `""`.
        suffix (str, optional): String shown after the unit. Defaults to `""`.

    Returns:
        (str): A human-readable number.
               Can be in bytes, kilobytes, megabytes, gigabytes, terabytes,
               petabytes, exabytes, zettabytes or yottabytes.

    Examples:
        >>> utils.bytes2human(8196)
        '8.0K'

        >>> utils.bytes2human(26684646897, prefix=" ", suffix="B")
        '24.9 GB'

        >>> utils.bytes2human(1 << 80)
        '1.0Y'
    """
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


def count_posts(tags=None, client=config.CLIENT):
    """Return the number of posts for given tags.

    Args:
        tags (str, optional): The desired tag search to get a count for.
            If this is None, the post count for the entire booru will be shown.
            Default: None.

    Returns:
        (int): The number of existing posts with given tags.
            If the number of tags used exceeds the maximum limit
            (2 for visitors and normal members on Danbooru), return `0`.

    Examples:
        >>> utils.count_posts() > 1000
        True

        >>> utils.count_posts("hakurei_reimu date:2017-09-17")
        5

        >>> utils.count_posts("hakurei_reimu maribel_hearn usami_renko")
        0
    """
    response = net.booru_api(client.count_posts, tags)
    if response != []:
        return response["counts"]["posts"]
    return None
