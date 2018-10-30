# lunakit

[![PyPI downloads](http://pepy.tech/badge/lunakit)](
    http://pepy.tech/project/lunakit)
[![PyPI version](https://img.shields.io/pypi/v/lunakit.svg)](
    https://pypi.org/projects/lunakit)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/lunakit.svg)](
    https://pypi.python.org/pypi/lunakit)


<SHORTDESC>

## kanarip incompatibilities

- New default directory structure (can be changed): _<id>/<resource>.<ext>_
- If a media's extension can't be determined, it will be saved with _.None_
- No more errored files dir
- Full info JSONs are saved instead of just a list of tag
- Full artcom and notes JSONs are downloaded
- The special information in meta files is now in info.json files

* kanarip couldn't fetch notes for posts created in the last 24h

## CLI examples

```sh
    $ lunakit
```

## Python package examples

```python3
    >>> import lunakit

    >>> 
```

## Installation

Requires Python 3.6+, tested on GNU/Linux only.

```sh
    # pip3 install lunakit
```
