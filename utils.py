def filter_duplicate_dicts(_list):
    # Convert the list of dictionaries to a list of tuples, tuples contain
    # items of the dictionary.
    # Since the tuples can be hashed, duplicates can be removed using a set.
    # After that, re-create the dictionaries from tuples with dict.
    return [dict(t) for t in set([tuple(_dict.items()) for _dict in _list])]
