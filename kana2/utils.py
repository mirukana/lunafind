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

    Can be used with:
        argparse.ArgumentParser(formatter_class=CapitalisedHelpFormatter)
    """
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = "Usage: "
        return super(CapitalisedHelpFormatter, self).add_usage(
            usage, actions, groups, prefix
        )


def filter_duplicate_dicts(list_):
    json_set = {json.dumps(dict_, sort_keys=True) for dict_ in list_}
    return [json.loads(dict_) for dict_ in json_set]


def bytes2human(size, prefix="", suffix=""):
    """Transform bytes size to a more readable way.

    Args:
        size (int): The size in bytes;
        prefix: What is shown before the unit;
        suffix: What is shown after the unit.

    Returns:
        Returns how many (unit) exist in (size).

        If size >= 2 ** 80, it will return in yotabytes.

        note: (size) must be < 2 ** 1024, else it will make a stack
        overflow.

    Examples:
        >>> utils.bytes2human(8196)
        '8.0K'
        >>> utils.bytes2human(16 * 1024, suffix="B", prefix=" ")
        '16.0 KB'
        >>> utils.bytes2human(1 << 32)
        '4.0G'
    """
    for unit in "B", "K", "M", "G", "T", "P", "E", "Z":
        if abs(size) < 1024.0:
            return "%3.1f%s%s%s" % (size, prefix, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s%s" % (size, prefix, "Y", suffix)


def make_dirs(*args):
    """Create directories in given path.
    It will be created parental levels if the path depth does not exist.

    Args:
        *args: The path of directory

    Examples:
        To make a directory in the current working directory, you must use
        relative path:

        >>> utils.make_dirs("year")
        >>> utils.makedirs("year/month/day", "week/hour/century")


        Or you can use absolute path:

        >>> utils.makedirs("/home/backup", "/etc/conf")
    """
    for dir_ in args:
        if not os.path.exists(dir_):
            os.makedirs(dir_, exist_ok=True)


def get_file_md5(file_path, chunk_size=16 * 1024 ** 2):
    """Generates a file's MD5 hash.

    Args:
        file_path: Where the file is.
        chunk_size (int): The size of the chunk to be loaded to RAM.
            Default = 16MB (16 * 1024 ** 2)

    Returns:
        (str) The MD5 hash of the given file.

    Examples:
        >>> utils.get_file_md5("kana2/query.py")
        '77af6728279fb6357671be4faba53de8'
    """
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as file_:
        while True:
            data = file_.read(chunk_size)
            if not data:
                break
            hash_md5.update(data)

    return hash_md5.hexdigest()
