# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

r"""Usage: lunafind [QUERY]... [options]

Search, filter and download posts from Danbooru-based sites.
Local directories containing downloaded posts can also be indexed and searched.

Part of the lunakit tools.
See also `lunasync` to easily download and keep in sync particular tags,
similar to Danbooru subscriptions: `https://github.com/mirukan/lunasync`

Arguments:
  QUERY
    Tags to search for. If unspecified, latest posts will be returned.

    Use the `-q`/`--query-location` option to take a search results URL,
    post URL, post resource path, or post directory path instead.

    As multiple queries can be used in one command,
    remember to quote searches with spaces (e.g. multiple tags).

    If a query starts with a `-`, prefix it with a `%` or `\` to prevent it
    from being seen as an option, e.g. `lunafind %-rating:e`.
    For `\`, quoting will always be required to prevent the shell from
    interpreting it.

Options:
  -q, --query-location
    Take booru search results URL, post URL, local post directory or
    resource path as `QUERY` instead of search tags.

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
    After 5 fatal timeouts (which are each retried a few times), the search
    will give up and return what was found until then.

    The default for local directories is infinite (`-1`), so the `-p`/`--pages`
    option will have no special effect unless a limit is set.

  -r, --random
    Get results in a randomized order.
    For local posts, all results have to be loaded in RAM in order to be
    effectively randomized, this could take some time.

  -w, --raw
    Do not parse the query for aliased tags, metatags or multiple tags,
    send it as a single literal tag.

  -s SOURCE, --source SOURCE
    Where to search posts.
    Can be the name of a booru defined in your configuration file,
    or the path to a folder containing downloaded posts.

    If a relative folder with the same name as a booru is used as `SOURCE`,
    e.g. `danbooru`, use `./danbooru` instead to indicate that it's a path.

    If not specified, the default booru from your config file is used.
    This option is ignored for URL/path queries with `q`/`--query-location`.


  -f TAGS, --filter TAGS
    Filter posts returned by searches,
    can be used to work around the two tags limit on Danbooru.
    Same syntax as tag searches, most metatags are supported with some
    additions and restriction lifts (to document).

    For a faster filtering, use tags that have less posts for the booru
    search and others for the filter, for example:
      `lunafind "snow wallpaper" -f "touhou 1girl" -D`
    Instead of:
      `lunafind "touhou 1girl" -f "wallpaper snow" -D`

  -m, --partial-match
    For `--filter` tags or `--source local` search queries,
    make every tag act like they are surrounded by wildcards, e.g.:
      `lunafind red -m -s local`
    would return results for tags like `red`, `red_eyes`, `bored`, etc, instead
    of just `red`.

    This allows, for example, to type only a character's first name and still
    get expected results.

  -o BY, --order BY
    Order posts returned by searches.
    Has to force all results to be fetched at the start and loaded in RAM.
    See `--help-order-values` to get a list of the possible `BY` values.

    Also remember this works with actually fetched results.
    The equivalent to searching "tag1 tag2 order:score" on Danbooru would be:
    `lunafind "tag1 tag2" --pages all --order score` (notice `--pages all`).


  -R RESOURCE, --resource RESOURCE
    Posts resource to print on stdout, default is `info`.
    Can be `info`, `media`, `artcom` or `notes`.

  -S RESOURCE, --show-location RESOURCE
    If `RESOURCE` is `post`: print the URL or directory path of posts.
    If `RESOURCE` is `info`, `media`, `artcom` or `notes`:
    print the URL or file path of that resource for posts.

  -A, --absolute-path
    Print absolute paths for `-S`/`--show-location`, resolving any symlinks.
    This can be a lot slower than printing normal relative paths.

  -D DIR, --download DIR
    Save posts and their resources (media, info, artcom, notes) to a folder.
    With `-D .` for example, info for post 1 on Danbooru would be saved
    at `./danbooru-1/info.json`.
    Any missing directory is created.
    Has no effect for posts from local directories.

    Do not rename the downloaded post directories (`<booru>-<id>`),
    or they will not be able to be searched locally.

  -Q, --quiet-skip
    Do not warn when skipping download of already existing files.

  -O, --overwrite
    Force download and overwrite any files that already exist.


  --print-config-path
    Show the configuration file path.
    If the file doesn't exist, a default one is automatically copied.

  -C PATH, --config PATH
    Use `PATH` as configuration file instead of the default location.

  --help-order-values
    Show possible values for `-o`/`--order`.

  -h, --help
    Show this help.

  -V, --version
    Show the program version.

Notes:
  Pixiv ugoiras
    The converted webm seen in the browser will be downloaded,
    instead of the heavy and unplayable zip files normally provided by the
    Danbooru API.

  Info JSON keys
    The info returned for posts contains `fetched_at` (date) and
    `fetched_from` (booru name) keys not present in the standard API returns.

    Posts returned from local directories will not have the
    `keeper_data` and `pixiv_ugoira_frame_data` keys, they are not indexed
    for performance reasons.

  Decensooru
    Censored posts from Danbooru/Safebooru (banned artists and tags) are
    automatically fixed when possible, using Decensooru's database.

Examples:
  lunafind "blonde 2girls" --limit 200 --pages all --download .
  ⋅                        -l          -p          -D
    Download all pages of posts containing tags `blonde` and `2girls` to the
    current directory. Don't forget the quotes for tags.
    See the `-l`/`--limit` option description to know why `200` is used here.

  lunafind https://safebooru.donmai.us/posts/1667182 --query-location
  ⋅                                                  -q
    Print info for the post at this URL.
    If it was a downloaded post, its directory should be used instead of URL.

  lunafind id:1667182 --query-location
  ⋅                   -q
    Print info for post with ID 2092692 (same result as URL example above).

  lunafind "blonde 2girls" --source . --show-location media
  ⋅                        -s         -S
    Print image/webm path of all posts with the tags `blonde` and `2girls`
    downloaded in the current directory.

  lunafind --show-location post
  ⋅        -S
    Print URL of the latest posts on the home page.

  lunafind translated --resource notes
  ⋅                   -R
    Print notes JSON for latest posts with the tag `translated`.

  lunafind --random --limit 100 | jq .id
  ⋅        -r       -l
    Print the ID of 100 random posts,
    using `jq` to display the `id` key of each info JSON.

  lunafind wallpaper --pages all --filter "%-no_human ratio:16:9 width:>=1920"
  ⋅                  -p          -f
    Retrieve all posts with the `wallpaper` tags,
    filter them to only leave those without the `no_human` tag, with a ratio
    of 16:9 and a width equal or superior to 1920, print info.

    Since the filter value starts with a `-`, it is escaped with a `%` to not
    be mistaken for an option. `\` can also be used, but will most likely
    always require quoting due to the shell.

  lunafind "~scenery ~landscape" "~outdoor ~nature" --pages 1-10 --download .
  ⋅                                                 -p           -D
    Do two separate searches (because of Danbooru two tag limit) for
    "scenery OR landscape" and "outdoor OR nature", pages 1 to 10,
    combine the results and download everything."""

import re
import sys
from types import GeneratorType
from typing import List, Optional

import docopt
from colorama import Fore

from . import LOG, Album, Stream, __about__, config, order, utils

OPTIONS = [string for match in re.findall(r"(-.)(?:\s|,)|(--.+?)\s", __doc__)
           for string in match if string]


def print_order_values() -> None:
    dicts     = {**order.ORDER_NUM, **order.ORDER_DATE, **order.ORDER_FUNCS}
    by_maxlen = len(max(dicts.keys(), key=len))

    for di in (order.ORDER_NUM, order.ORDER_DATE):
        print(f"{Fore.MAGENTA}{'Value':{by_maxlen}}  Default sort{Fore.RESET}")

        for by, (asc_or_desc, _) in di.items():
            print(f"{Fore.BLUE}{by:{by_maxlen}}{Fore.RESET}  "
                  f"{asc_or_desc}ending")

        print()

    print("For values above, the sort order can be manually specified by "
          "prefixing the value with 'asc_' or 'desc_', e.g. 'asc_score'.\n")

    for by in order.ORDER_FUNCS:
        print(f"{Fore.BLUE}{by}{Fore.RESET}")

    sys.exit(0)


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]

    try:
        args = docopt.docopt(
            __doc__, help=False, argv=argv, version=__about__.__version__
        )
    except docopt.DocoptExit:
        LOG.error(f"Invalid command syntax or bad option, check --help.")
        sys.exit(10)

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
        "limit":  int(args["--limit"]) if args["--limit"] else None,
        "random": args["--random"],
        "raw":    args["--raw"],
        "client": args["--source"],
    }

    params = {k: v for k, v in params.items() if v is not None}

    unesc = lambda s: s[1:] if s.startswith(r"\-") or s.startswith("%-") else s

    stores = [
        Stream(unesc(q),
               **params,
               location     = args["--query-location"],
               partial_tags = args["--partial-match"])
        .filter(unesc(args["--filter"] or ""),
                partial_tags = args["--partial-match"])
        for q in args["QUERY"] or ("",)
    ]

    if args["--order"]:
        stores = [
            sum([Album(s) for s in stores], Album()).order(args["--order"])
        ]


    if not (args["--resource"] or args["--show-location"] or
            args["--download"]):
        args["--resource"] = "info"

    for obj in stores:
        posts = obj.list if isinstance(obj, Album) else obj

        if args["--download"]:
            posts.download(base_dir  = args["--download"],
                           overwrite = args["--overwrite"],
                           warn      = not args["--quiet-skip"])
            continue

        try:
            for post in posts:
                if args["--show-location"]:
                    path = post.get_location(
                        args["--show-location"],
                        absolute = args["--absolute-path"]
                    )
                    if path:
                        print(path, flush=True)
                    continue

                res_name = args["--resource"]
                res      = getattr(post, res_name) if res_name else post.info

                if res_name == "media" and isinstance(res, GeneratorType):
                    res = b"".join(res)

                if res and isinstance(res, bytes):
                    sys.stdout.buffer.write(res)
                    sys.stdout.flush()
                elif res:
                    print(utils.jsonify(res, indent=4), flush=True)
                else:
                    LOG.warning("Post %d has no %s resource.",
                                post.id, res_name)
        except (KeyboardInterrupt, BrokenPipeError):
            sys.exit(130)
