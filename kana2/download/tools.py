import sys
import os
import json


def load_infos(infos=None):
    if infos:
        return json.loads(infos)

    # TODO: accept python dict from ./query
    if not os.isatty(0):  # If something is piped
        return json.load(sys.stdin)

    if os.path.isfile(sys.argv[-1]):
        return json.load(open(sys.argv[-1]))

    # TODO: print help


def get_file_to_dl_ext(postDict):
    # TODO: Config option to download normal zip instead.
    try:
        if postDict["file_url"].endswith(".zip"):
            return postDict["large_file_url"].split(".")[-1]
        return postDict["file_ext"]
    except KeyError:
        return "unknown"


def dl_size(postList):
    return sum(post["file_size"] for post in postList)
