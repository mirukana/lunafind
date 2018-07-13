"""Various global variables, functions and others specially used for kana2."""

import hashlib
import json
import logging as log
import os
import re

from . import CHUNK_SIZE, CLIENT, net


def _check_can_write(can_overwrite, path):
    if not can_overwrite and os.path.exists(path):
        log.warning(f"File {path} already exists, will not overwrite.")
        return False
    return True


def write(content, to_path, mode="w", overwrite=False):
    if not _check_can_write(overwrite, to_path):
        return False

    with open(to_path, mode) as output:
        output.write(content)

    return True


def write_chunk(content_iter, to_path, mode="w", overwrite=False):
    if not _check_can_write(overwrite, to_path):
        return False

    with open(to_path, mode) as output:
        for chunk in content_iter:
            output.write(chunk)

    return True


def load_file(in_path, mode="r", chunk_size=CHUNK_SIZE):
    with open(in_path, mode) as input_:
        while True:
            data = input_.read(chunk_size)
            if not data:
                break
            yield data


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


def count_posts(tags=None, client=CLIENT):
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


def client_return(normal_returns, client):
    return normal_returns if client is CLIENT else normal_returns, client


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


def get_file_md5(file_path, chunk_size=CHUNK_SIZE):
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
    if not indent:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False)

    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=4)


def dict_has(dict_, *keys):
    return set(keys) <= set(dict_)
