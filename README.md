# lunafind

[![PyPI downloads](http://pepy.tech/badge/lunafind)](
    http://pepy.tech/project/lunafind)
[![PyPI version](https://img.shields.io/pypi/v/lunafind.svg)](
    https://pypi.org/projects/lunafind)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/lunafind.svg)](
    https://pypi.python.org/pypi/lunafind)

Search, filter, inspect, download posts from Danbooru/Safebooru and find them
back from the command line without setting up any service or database.

Suitable for daily terminal usage, usable for scripts and as a library
for Python 3.6+.

See also [lunasync](https://github.com/mirukan/lunasyc) to automatically
download and keep in sync particular tags using **lunafind**,
similar to Danbooru tag subscriptions or saved searches.

## Features

- Operate on tag searches, URLs or file paths
- Combine results from multiple searches
- Banned/hidden posts are automatically
  [decensored](https://github.com/mirukan/pydecensooru) when possible
- Specify custom page ranges, or just get everything
- Filter and order booru results to work around the two tags search limit
- Optional partial/fuzzy tag matching for filter and local searches
- Search downloaded posts by tags as if they were on a booru, without the
  hassle of setting up one
- Instant results from local searches in most cases after indexing
- Fast multithreaded downloads, 8 downloads in parallel by default
- Supports operating on post media (image, ugoira WebM, etc), info, notes,
  artist commentaries:
  - Getting the URLs or file/folder paths
  - Printing on standard output
  - Downloading

## Local searches performance

The first time a local post search is done, an index file to speed up future
searches will be automatically created and updated when new post directories
exist or are removed.

Tests with ~165 000 posts in the same directory,
a CPU with average single-core performance
(AMD FX-8300 - there is no benefit yet from multiple cores),
generic 7200 RPM hard disk, BTRFS file system, Void Linux 4.18.14 x86\_64:  
- It takes about 2m30s - 3m to index everything from scratch.  
- After this, search results start coming instantly unless `--random` or
  `--order` is used.  
- Searches finish completely in 8-20s.

## Command line usage

Downloading to the current folder every post tagged *blonde* and *2girls*
(default booru is <https://danbooru.donmai.us>):

```sh
    lunafind "blonde 2girls" --limit 200 --pages all --download .
```

Searching through the posts we just downloaded,
printing image paths for the results:

```sh
    lunafind "blonde blue_eyes rating:s score:>5" --source . --show-location media
```

See `lunafind --help` for all options and examples.

## Python usage

No real documentation yet. Three main classes are provided:

- `Post`: represents a local or remote single post, with its info, media, notes
          and artcom (artist commentary).

- `Album`: works like a dictionary of `Post`, where keys are the post IDs.
           Has magic methods and operators to facilitate working with them.
           Can be filtered, ordered and downloaded, and more.

- `Stream`: an efficiant lazy iterator yielding posts.
            Can be filtered and multithread-downloaded.

Reproducing the command line examples in the section above:

```python3
    from lunafind import Stream

    Stream("blonde 2girls", limit=200, pages="all").download()

    for post in Stream("blonde blue_eyes rating:s score:>5", client="."):
        print(post.get_location("media"))
```

## Installation

Requires Python 3.6+ and pip (for automatic easy install).  
Tested on GNU/Linux only right now, but should work on other common OS.  
As root:

```sh
    pip3 install -U lunafind
```
