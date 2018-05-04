# kana2 TODO list

- reqwrap.py
  - More readable True/False → "true"/"false"
  - Put random/raw/etc filtering in info.py or query.py instead

- Library usability improvements
    - Functions: Just take a query as arg? e.g. info.abettername("rumia")
    - Multiple args instead of having to write a dict? e.g. func("rumia", 20)
    - Some way to avoid the ))[0])))[0])))))) mess?

- Use Python 3.6+ new f"string {some_var}" interpolation when possible 

- Break download.one\_post() into smaller functions

- Multi proc media notes artcom?
- Handle connection errors at multiprocessing functions levels

- Prettier logging

- Merge tools.py and utils.py?

- General code
    - Enforce static variable types, especially for function arguments
      - Maybe with [mypy](https://github.com/python/mypy)?
    - See about CPython and Pipy
    - Use [attrs](http://www.attrs.org/en) for better classes
    - \_private\_functions with a magic leading underscore

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

- Better logging, also order correctly query things

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
