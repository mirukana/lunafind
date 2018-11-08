# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

r"""Usage: lunakit [QUERY]... [options]

Search, filter and download posts from Danbooru-based sites.

Arguments:
  QUERY
    Tags to search for, search results URL, or post URL.
    If no queries are used, latest posts from the home page will be returned.

    As multiple queries can be used in one command,
    tag searches with multiple tags must be wrapped in quotes.

    If a query starts with a `-`, prefix it with a `%` or `\` to prevent it
    from being seen as an option, e.g. `lunakit %-rating:e`.
    For `\`, quoting will always be required to prevent the shell from
    interpreting it.

Options:
  -p PAGES, --pages PAGES
    Pages to fetch for tag searches, can be:
    - All pages from start to end: `all`
    - A direct number for a single page, e.g. `1` (the default)
    - A range with an optional step: `3-6`, `10-end`, `1-20-2` (skip 1/2 pages)
    - A comma-separated list of pages: `1,3,5,12,99`

  -l NUM, --limit NUM
    Number of posts per page.
    For Danbooru, default is `20`, max is `200`, and the max page with the
    default limit for non-premium users is `1000`.

    Using `--limit 200` allows more total posts to be fetched,
    20K vs 80K with some big tags. Timeouts start to appear near pages 400-500.

    The default for local directories is infinite (`-1`), so the `--pages`
    option will have no special effect unless a limit is set.

  -r, --random
    Get results in a randomized order.

  -w, --raw
    Do not parse the query for aliased tags, metatags or multiple tags,
    send it as a single literal tag.

  -s NAME, --source NAME
    Where to search posts.
    Can be the name of a booru defined in your configuration file,
    or `local` to search downloaded posts in the current directory.

    If not specified, the default booru from your config file is used.
    This option is ignored for URL queries.

  -P PATH, --local-path PATH
    Path to the directory containing the posts for `--source local`.
    If unspecified, the current directory (`.`) is used.


  -f TAGS, --filter TAGS
    Filter posts returned by searches,
    can be used to work around the two tags limit on Danbooru.
    Same syntax as tag searches, most metatags are supported with some
    additions and restriction lifts (to document).

    For a faster filtering, use tags that have less posts for the booru
    search and others for the filter, for example:
      `lunakit "snow wallpaper" -f "touhou 1girl" -d`
    Instead of:
      `lunakit "touhou 1girl" -f "wallpaper snow" -d`

  -o BY, --order BY
    Order posts returned by searches.
    Has to force all results to be fetched at the start and loaded in RAM.
    See `--help-order-values` to get a list of the possible `BY` values.

    Also remember this works with actually fetched results.
    The equivalent to searching "tag1 tag2 order:score" on Danbooru would be:
    `lunakit "tag1 tag2" --pages all --order score` (notice `--pages all`).


  -R RES, --resource RES
    Posts resource to print on stdout;
    can be `info`, `media`, `artcom` or `notes`.

    If no `--resource`, `--show-key` or `--download` option is specified,
    the default behavior is `--resource info`.

  -k KEY, --show-key KEY
    Comma-separated list of info JSON keys to print for posts,
    e.g. `dl_url` or `id,tag_string`.
    If multiple keys are specified, posts will be separated by a blank line.

  -d, --download
    Save posts and their resources (media, info, artcom, notes...) to disk.
    Cannot be used with `--resource` or `--show-key`.
    Has no effect for posts from `--source local`.

  -q, --quiet-skip
    Do not warn when skipping download of already existing files.

  -O, --overwrite
    Force download and overwrite any files that already exist.


  --print-config-path
    Show the configuration file path.
    If the file doesn't exist, a default one is automatically copied.

  --config PATH
    Use `PATH` as configuration file instead of the default location.

  --help-order-values
    Show possible values for `--order`.

  -h, --help
    Show this help.

  -V, --version
    Show the program version.

Notes:
  Pixiv ugoiras
    The converted webm seen in the browser will be downloaded,
    instead of the heavy and unplayable zip files normally provided by the
    Danbooru API.

  Additional info keys
    The info returned for posts contains `fetched_at` (date) and
    `fetched_from` (booru name) keys not present in the standard API returns.

Examples:
  lunakit "blonde 2girls" --limit 200 --pages all --download
    Download all pages of posts containing tags `blonde` and `2girls`.
    See the `--limit` option description to know why `200` is used here.

  lunakit --show-key title,post_url
    Print title and post page URL for latest posts on the home page.

  lunakit --random --limit 200 --show-key dl_url
    Print raw image/webm URL for 200 random posts.

  lunakit wallpaper --pages all --filter "%-no_human ratio:16:9 width:>=1920"
    Retrieve all posts with the `wallpaper` tags,
    filter them to only leave those without the `no_human` tag, with a ratio
    of 16:9 and a width equal or superior to 1920, print info.

    Since the filter value starts with a `-`, it is escaped with a `%` to not
    be mistaken for an option. `\` can also be used, but will most likely
    always require quoting due to the shell.

  lunakit "~scenery ~landscape" "~outdoor ~nature" --pages 1-10 --download
    Do two separate searches (Danbooru 2 tag limit) for "scenery or landscape"
    and "outdoor or nature", pages 1 to 10, combine the results and
    download everything."""

import re
import sys
from typing import List, Optional

import docopt

from . import (LOG, TERM, Album, Stream, __about__, clients, config, order,
               utils)

OPTIONS = [string for match in re.findall(r"(-.)(?:\s|,)|(--.+?)\s", __doc__)
           for string in match if string]


def print_order_values() -> None:
    dicts     = {**order.ORDER_NUM, **order.ORDER_DATE, **order.ORDER_FUNCS}
    by_maxlen = len(max(dicts.keys(), key=len))

    for di in (order.ORDER_NUM, order.ORDER_DATE):
        print(f"{'Value':{by_maxlen}}   Default sort")

        for by, (asc_or_desc, _) in di.items():
            print(f"{by:{by_maxlen}}  {asc_or_desc}ending")

        print()

    print("For values above, the sort order can be manually specified by "
          "prefixing the value with 'asc_' or 'desc_', e.g. 'asc_score'.\n")

    for by in order.ORDER_FUNCS:
        print(by)

    sys.exit(0)


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]

    try:
        args = docopt.docopt(
            __doc__, help=False, argv=argv, version=__about__.__version__
        )
    except docopt.DocoptExit:
        if len(sys.argv) > 1:
            print(TERM.red("Invalid command syntax, check help:\n"))

        utils.print_colored_help(__doc__, exit_code=10)

    if args["--config"]:
        config.FILE = args["--config"]
        config.reload()

    if args["--help-order-values"]:
        print_order_values()

    if args["--help"]:
        utils.print_colored_help(__doc__)

    if args["--print-config-path"]:
        print(config.FILE)
        sys.exit()


    params = {
        "pages":  args["--pages"],
        "random": args["--random"],
        "raw":    args["--raw"],
    }

    params = {k: v for k, v in params.items() if v is not None}

    if args["--limit"]:
        params["limit"] = int(args["--limit"])

    if args["--source"] == "local":
        params["prefer"] = clients.local.Local(path=args["--local-path"])
    elif args["--source"]:
        params["prefer"] = clients.net.ALIVE[args["--source"]]

    unesc = lambda s: s[1:] if s.startswith(r"\-") or s.startswith("%-") else s

    stores = [Stream(unesc(q), **params).filter(unesc(args["--filter"] or ""))
              for q in args["QUERY"] or [""]]

    if args["--order"]:
        stores = [
            sum([Album(s) for s in stores], Album()).order(args["--order"])
        ]

    for obj in stores:
        posts = obj.list if isinstance(obj, Album) else obj

        if not(args["--resource"] or args["--show-key"] or args["--download"]):
            args["--resource"] = "info"

        if args["--download"]:
            posts.write(overwrite = args["--overwrite"],
                        warn      = not args["--quiet-skip"])
            continue


        newline = bool(args["--show-key"] and "," in args["--show-key"]) or \
                  bool(args["--resource"])

        for post in posts:
            if args["--show-key"]:
                for key in args["--show-key"].split(","):
                    try:
                        print(post.info[key])
                    except KeyError:
                        LOG.warning("Post %d has no %r key.", post.id, key)

            if args["--resource"]:
                res = getattr(post, args["--resource"])

                if res and isinstance(res, bytes):
                    print(res, end="", flush=True)
                elif res:
                    print(utils.pretty_print_json(res))
                else:
                    LOG.warning("Post %d has no %s.",
                                post.id, args["--resource"])

            if newline:
                print()
