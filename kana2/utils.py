"""General useful classes, functions and others used in kana2."""
import argparse
import hashlib
import json
import os
import signal
import sys

# Must be effective ASAP, hide traceback when hitting CTRL-C (SIGINT).
signal.signal(signal.SIGINT, lambda signal_nbr, _: sys.exit(128 + signal_nbr))


class CapitalisedHelpFormatter(argparse.HelpFormatter):
    """ Display argparse's help with a capitalized "usage:".

    Example:
        argparse.ArgumentParser(formatter_class=CapitalisedHelpFormatter)
    """
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = "Usage: "

        return super(CapitalisedHelpFormatter, self).add_usage(
            usage, actions, groups, prefix)


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
    for unit in "B", "K", "M", "G", "T", "P", "E", "Z":
        if abs(size) < 1024.0:
            return "%3.1f%s%s%s" % (size, prefix, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s%s" % (size, prefix, "Y", suffix)


def make_dirs(*args):
    """Create directories as needed for a given path.

    Args:
        *args (str): New directory absolute or relative path.

    Examples:
        >>> import os
        >>> os.chdir("/tmp")
        >>> utils.make_dirs("foo/bar/lorem")
        >>> os.path.exists("/tmp/foo/bar/lorem")
        True
    """
    for dir_ in args:
        if not os.path.exists(dir_):
            os.makedirs(dir_, exist_ok=True)


def get_file_md5(file_path, chunk_size=16 * 1024 ** 2):
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
