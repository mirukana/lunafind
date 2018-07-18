# kana2 TODO list

- Store ideas:
  - Cleaner implementation of Post functions
  - Store filtering: x.filter(tags or other stuff), or with operators?
    - Blacklist
    - Tag and JSON conditions
    - Sort by specific key, ascending or descending
    - Max number of posts
  - Optionally use generators to avoid storing in RAM
  - Manage both local .writen() and remote booru posts?
    - Make sure tuples (lists in json) are parsed back as tuples     

- Prettier logging

- Refactor net and errors modules
    - See about HTTPAdaptor and urllib Timer
- Retry download on verify failure

- Multiple pages search
  - Estimate posts total for a search

- ujson, simplejson
- Enforce static variable types
  - Maybe with [mypy](https://github.com/python/mypy)?
- See about CPython and Pipy

- Multiprocessing
  - requests-threads, requests-futures, grequests, zproc, async/await?

- Thumbnails?

- Do something about parent/child posts

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
