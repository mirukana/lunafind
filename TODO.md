# kana2 TODO list

- Store ideas:
    - Cleaner implementation of Post functions
    - x = Store(...); x[all].function → operates on all posts?
    - Store filtering: x.filter(tags or other stuff), or with operators?
    - Manage both local .writen() and remote booru posts?

- Prettier logging
- Log info functions

- Refactor net and errors modules
    - See about HTTPAdaptor and urllib Timer
- Clean up utils.py
- Is attr lib for Post really useful?

- Multiple pages search
- Enforce static variable types
  - Maybe with [mypy](https://github.com/python/mypy)?
- See about CPython and Pipy

- Multiprocessing
  - requests-threads, requests-futures, grequests, zproc, async/await?

- filter.py
    - Duplicates
    - Blacklist
    - Tag conditions
    - "JSON" conditions
    - Sort by specific key, ascending or descending
    - Max number of posts

- Thumbnail script

- Do something about parent/child posts

- D O C S T R I N G S
    - Generate docs and manpages with Sphinx
- T E S T S

- CLI script
    - [termcolor](https://pypi.python.org/pypi/termcolor), used in **halo**
    - zplug-like UI for multiprocess downloading?
    - Use [doctopt](https://docopt.readthedocs.io/en/latest/)
    - Config system
    - Auto filter
    - Ignore and error lists
    - bash/zsh completitions

- Other programs
    - Tag subs management
