import logging
from pprint import pprint

from . import args
from . import query


def main():
    logging.basicConfig(level=logging.INFO)

    args.parsed = args.parse()

    if args.parsed.pretty_print and args.parsed.json:
        print(query.multiple(args.parsed.query[0], toJson=True, jsonIndent=4))
    elif args.parsed.pretty_print and not args.parsed.json:
        pprint(query.multiple(args.parsed.query[0], toJson=False), indent=4)
    else:
        print(query.multiple(args.parsed.query[0], toJson=args.parsed.json))


main()
