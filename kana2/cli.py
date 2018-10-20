# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"""Usage: kana2 [options] ARG1

<SHORTDESC>

Arguments:
  ARG1  ...

Options:
  -h, --help     Show this help.
  -V, --version  Show the program version.

Examples:
  kana2 ARG1
    ..."""

import sys
from typing import List, Optional

import docopt

from . import __about__


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]

    try:
        args = docopt.docopt(__doc__, argv=argv, version=__about__.__version__)
    except docopt.DocoptExit:
        if len(sys.argv) > 1:
            print("Invalid command syntax, check help:\n")

        main(["--help"])
        sys.exit(1)

    print(args)
