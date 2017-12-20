import argparse
from pybooru.api_danbooru import DanbooruApi_Mixin


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


def count_posts(self, tags):
    """
    Return the total number of posts on the booru, or the number for a
    specific tag search if a tags parameter is passed.
    Missing function added pybooru's Danbooru API.
    """
    return self._get("counts/posts.json", {"tags": tags})


DanbooruApi_Mixin.count_posts = count_posts
