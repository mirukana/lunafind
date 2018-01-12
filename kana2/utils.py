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
    for unit in "B", "K", "M", "G", "T", "P", "E", "Z":
        if abs(size) < 1024.0:
            return "%3.1f%s%s%s" % (size, prefix, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s%s" % (size, prefix, "Y", suffix)


def make_dirs(*args):
    for dir_ in args:
        if not os.path.exists(dir_):
            os.makedirs(dir_, exist_ok=True)


def get_file_md5(file_path, chunk_size=16 * 1024 ** 2):
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as file_:
        while True:
            data = file_.read(chunk_size)
            if not data:
                break
            hash_md5.update(data)

    return hash_md5.hexdigest()
