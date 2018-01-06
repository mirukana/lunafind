import signal
import os
import sys
import argparse
import cursor  # TODO: Remove when halo issue #41 is fixed.
import hashlib


def abort_script(signalNbr=2):
    cursor.show()  # TODO: Remove when halo issue #41 is fixed.
    sys.exit(128 + signalNbr)


# Must be effective ASAP. Hide traceback when hitting CTRL-C (sends SIGINT).
signal.signal(signal.SIGINT, lambda signalNbr, _: abort_script(signalNbr))


class CapitalisedHelpFormatter(argparse.HelpFormatter):
    """
    Display argparse's help with a capitalized "usage:".
    Use with:
        argparse.ArgumentParser(formatter_class=CapitalisedHelpFormatter)
    """
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = "Usage: "
        return super(CapitalisedHelpFormatter, self).add_usage(
            usage, actions, groups, prefix
        )


def bytes2human(size, prefix="", suffix=""):
    for unit in "B", "K", "M", "G", "T", "P", "E", "Z":
        if abs(size) < 1024.0:
            return "%3.1f%s%s%s" % (size, prefix, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s%s" % (size, prefix, "Y", suffix)


def make_dirs(*args):
    for _dir in args:
        if not os.path.exists(_dir):
            os.makedirs(_dir, exist_ok=True)


def get_file_md5(filePath, chunkSize=16 * 1024 ** 2):
    hash_md5 = hashlib.md5()

    with open(filePath, "rb") as _file:
        while True:
            data = _file.read(chunkSize)
            if not data:
                break
            hash_md5.update(data)

    return hash_md5.hexdigest()
