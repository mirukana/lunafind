import sys
import argparse


class CapitalisedHelpFormatter(argparse.HelpFormatter):
    """
    Display argparse's help with a capitalized "usage:".
    Use with:
        argparse.ArgumentParser(formatter_class=CapitalisedHelpFormatter)
    """
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = 'Usage: '
        return super(CapitalisedHelpFormatter, self).add_usage(
            usage, actions, groups, prefix
        )


def make_dirs(*args):
    for _dir in args:
        if not os.path.exists(_dir):
            os.makekdirs(_dir, exist_ok=True)


def info(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def update_line(string):
    sys.stderr.write("\r" + string)
    sys.stderr.flush()
