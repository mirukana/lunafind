# kana2

[![PyPI downloads](http://pepy.tech/badge/kana2)](
    http://pepy.tech/project/kana2)
[![PyPI version](https://img.shields.io/pypi/v/kana2.svg)](
    https://pypi.org/projects/kana2)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/kana2.svg)](
    https://pypi.python.org/pypi/kana2)


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
    $ kana2
```

## Python package examples

```python3
    >>> import kana2

    >>> 
```

## Installation

Requires Python 3.6+, tested on GNU/Linux only.

```sh
    # pip3 install kana2
```
