# kana2 TODO list

- Prettier logging

- ujson, simplejson
- Enforce static variable types
  - Maybe with [mypy](https://github.com/python/mypy)?
- See about CPython and Pipy

- Multiple pages search
  - Estimate posts total for a search

- Store ideas:
  - Cleaner implementation of Post functions
  - Store filtering: x.filter(tags or other stuff), or with operators?
    - Blacklist
    - Tag and JSON conditions
    - Sort by specific key, ascending or descending
    - Max number of posts
  - Lazy parameter to use generators for all get... functions
  - Manage both local .writen() and remote booru posts
    - Make sure tuples (lists in json) are parsed back as tuples     

- Multiprocessing
  - requests-threads, requests-futures, grequests, zproc, async/await?

- Thumbnails?

- Do something about parent/child posts

- When searching for >2 tags, automatically use filtering to transparently
  work around limits?
- Integrate Decensooru?

- D O C S T R I N G S
    - Generate docs and manpages with Sphinx
- T E S T S

- CLI script
    - [termcolor](https://pypi.python.org/pypi/termcolor), used in **halo**
      - Or maybe blessings?
    - zplug-like UI for multiprocess downloading?
    - Use [doctopt](https://docopt.readthedocs.io/en/latest/)
    - Config system
    - Auto filter
    - Ignore and error lists
    - bash/zsh completitions

- Other programs
    - Tag subs management
