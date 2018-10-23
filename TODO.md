# kana2 TODO list

- Finish implementing filter meta-tags

- Human-readable repls, show what resource posts have

- Implement all set operators for attridict

- If an http/booru error/ctrl-c happens, still return what was fetched right

- Manage both local .writen() and remote booru posts
  - Make sure tuples (lists in json) are parsed back as tuples     

- Some form of asynchronicity
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
    - zplug/emerge-like UI for multiprocess downloading?
    - Use [doctopt](https://docopt.readthedocs.io/en/latest/)
    - Config system
    - Auto filter
    - Ignore and error lists
    - bash/zsh completitions

- Other programs
    - Tag subs management
    - Tag aliases and relations
