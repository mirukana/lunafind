import logging

from . import dl
from . import tools


def main():
    logging.basicConfig(level=logging.INFO)
    dl.posts(tools.load_infos())
