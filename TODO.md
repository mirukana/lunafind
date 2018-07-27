# kana2 TODO list

- Always used requests chunked transfers
- Get rid of verify file size thing since chunked transfers will error on
- Catch errors in io.write() for chunked transfers
- Do something about media generator
  - Lazy parameter to use generators for all get... functions
    incomplete data?
- Manage both local .writen() and remote booru posts
  - Relative paths from the data.json
  - Make sure tuples (lists in json) are parsed back as tuples     
- utils.blank\_line() without having to have \_blank\_line function params?

- Prettier logging

- Save errors in Post

- Multiple pages search
- Estimate posts total for a search

- Store ideas:
  - Rename get functions to fetch.., to avoid setters/getters confusion
  - Post.paths as property with setter
  - Store filtering: x.filter(tags or other stuff), or with operators?
  - Blacklist
    - Tag and JSON conditions
    - Sort by specific key, ascending or descending
    - Max number of posts

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
    - zplug/emerge-like UI for multiprocess downloading?
    - Use [doctopt](https://docopt.readthedocs.io/en/latest/)
    - Config system
    - Auto filter
    - Ignore and error lists
    - bash/zsh completitions

- Other programs
    - Tag subs management
    - Tag aliases and relations

- See about PyPy when it will support Python 3.6
