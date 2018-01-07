import argparse

from . import tools

parsed = {}


def parse(args=None):
    """Define argument parser and return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
            description="Output post informations from a booru's API.",
            add_help=False,
            formatter_class=tools.CapitalisedHelpFormatter
    )

    parser._positionals.title = "Positional arguments"
    parser.add_argument(
            "query",
            action="append", nargs="+", metavar="QUERY",
            help="Tag search, post ID, post URL, search results URL or " +
                 " '%%' for the home page."
    )

    searchOpts = parser.add_argument_group("Search queries options")
    searchOpts.add_argument(
            "-p", "--page",
            nargs="+", default=1,
            help="Pages to fetch (default: %(default)d)\n" +
                 "Can be a single page or a range (e.g. 3-777, 1+ or +20)"
    )
    searchOpts.add_argument(
            "-l", "--limit",
            type=int, default=200,  # TODO: config for this
            help="Number of posts per page (default: %(default)d)"
    )
    searchOpts.add_argument(
            "-r", "--random",
            action="store_true",
            help="Request random posts from the booru."
    )
    searchOpts.add_argument(
            "-R", "--raw",
            action="store_true",
            help="Ask the booru to parse QUERY as a single literal tag."
    )

    parser._optionals.title = "General options"
    parser.add_argument(
            "-j", "--json",
            action="store_true",
            help="Output post informations as JSON."
    )
    parser.add_argument(
            "-P", "--pretty-print",
            action="store_true",
            help="Print the post infos in a human-readable way."
    )
    parser.add_argument(
            "-h", "--help",
            action="help", default=argparse.SUPPRESS,
            help="Show this help message and exit."
    )

    # Defaults to the function arguments, else CLI arguments.
    global parsed
    parsed = parser.parse_args(args if args else None)
    return parsed
