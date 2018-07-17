"""Various global variables, functions and others specially used for kana2."""

import hashlib
import json
import logging as log
import os
import re
import sys

from . import config, net


def write(content, to_path, mode="w", msg=None, chunk=False, overwrite=False):
    os.makedirs(os.path.dirname(to_path), exist_ok=True)

    if os.path.exists(to_path) and not overwrite:
        log.warning(f"File '{to_path}' already exists, will not overwrite.")
        return False

    if msg:
        log.info(msg)

    with open(to_path, mode) as output:
        if not chunk:
            output.write(content)
            return True

        for chunk_data in content:
            output.write(chunk_data)
    return True


def load_file(in_path, mode="r", chunk_size=config.CHUNK_SIZE):
    with open(in_path, mode) as input_:
        while True:
            data = input_.read(chunk_size)
            if not data:
                break
            yield data


def load_json(in_path):
    with open(in_path, "r") as json_file:
        return json.load(json_file)


def filter_duplicate_dicts(list_):
    """Return a list of dictionaries without duplicates.

    Args:
        list_ (list): List of dictionaries.

    Returns:
        (list): Filtered list.

    Examples:
        >>> utils.filter_duplicate_dicts([{"a": 1}, {"a": 3}, {"a": 3}])
        [{'a': 3}, {'a': 1}]
    """

    json_set = {json.dumps(dict_, sort_keys=True) for dict_ in list_}
    return [json.loads(dict_) for dict_ in json_set]



# TODO: Move this to filter.py
def filter_duplicates(posts):
    """Return a list of unique posts, duplicates are detected by post id.

    Args:
        posts (list): Post information dictionaries.

    Returns:
        posts (list): Post dictionaries without duplicates.

    Examples:
        >>> utils.filter_duplicates([{"id": 1}, {"id": 1}, {"id": 2}])
        [{'id': 1}, {'id': 2}]
    """

    id_seen = [None]
    for i, post in enumerate(posts):
        if post["id"] in id_seen:
            del posts[i]
        else:
            id_seen.append(post["id"])
    return posts


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

    return net.booru_api(client.count_posts, tags)["counts"]["posts"]


def replace_keys(post, string):
    if not isinstance(string, str):
        return string

    # Unless \ escaped: {foo} → Capture foo; {foo, bar} Capture foo and bar.
    return re.sub(r"(?<!\\)(?:\\\\)*{(.+?)(?:, ?(.+?))?}",
                  lambda match: str(post.get(match.group(1), match.group(2))),
                  string)


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
            return "%3.1f%s%s%s" % (size, prefix, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s%s" % (size, prefix, "Y", suffix)


def get_file_md5(file_path, chunk_size=config.CHUNK_SIZE):
    """Calculate a file's MD5 hash.

    Args:
        file_path (str): Path of the file to calculate hash.
        chunk_size (int, optional): Maximum size of a chunk to be loaded in
            RAM. Defaults to `16 * 1024 ** 2` (16 MB).

    Returns:
        (str): The MD5 hash of the given file.

    Examples:
        >>> utils.get_file_md5("/dev/null")
        'd41d8cd98f00b204e9800998ecf8427e'
    """
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as file_:
        while True:
            data = file_.read(chunk_size)
            if not data:
                break
            hash_md5.update(data)

    return hash_md5.hexdigest()


def flatten_list(list_):
    return [item for sublist in list_ for item in sublist]


def log_error(error):
    """Log an exception unless print_err is False, if existing"""
    try:
        if not error.print_err:
            return error.message  # Don't print it
    except AttributeError:  # If error has no print_err (not a kana2 error)
        pass

    log.error(error.message)
    return error.message


def jsonify(obj, indent=False):
    # Serialize Arrow date object:
    if "fetch_date" in obj:
        obj["fetch_date"] = (obj["fetch_date"]
                             .format("YYYY-MM-DDTHH:mm:ss.SSSZZ"))

    if not indent:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False)

    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=4)


def dict_has(dict_, *keys):
    return set(keys) <= set(dict_)


def expand_path(path):
    try:
        return os.path.expandvars(os.path.expanduser(path))
    except TypeError:  # e.g. Post.set_paths(something=False) → Bool, error
        return path


def blank_line():
    print(file=sys.stderr)
