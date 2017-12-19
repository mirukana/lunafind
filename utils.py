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


def filter_duplicate_dicts(_list):
    """
    Convert the list of dictionaries to a list of tuples, tuples contain
    items of the dictionary.
    Since the tuples can be hashed, duplicates can be removed using a set.
    After that, re-create the dictionaries from tuples with dict.
    """
    return [dict(t) for t in set([tuple(_dict.items()) for _dict in _list])]
