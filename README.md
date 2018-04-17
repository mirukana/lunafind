# Notes

## Install dependencies

(Pybooru with the right commits isn't released yet on pip.)

    sudo pip3 install https://git.io/vx2YG requests halo arrow whratio --upgrade

## kanarip v1 incompatibilities

- Save JSONS in info/ instead of generating tags/ and meta/
- Errored files structure: {info,media,etc}/failed/id.ext instead of errors/...
- Downloaded artcom and notes will no longer be wrapped in lists
- Download full artcom and notes

## TODO

- reqwrap.py
  - Custom exception instead of raising requests RetryError
  - More readable True/False → "true"/"false"
  - Put random/raw/etc filtering in info.py or query.py instead

- Library usability improvements
    - Functions: Just take a query as arg? e.g. info.abettername("rumia")
    - Multiple args instead of having to write a dict? e.g. func("rumia", 20)
    - Some way to avoid the ))[0])))[0])))))) mess?

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

## Tests to write

OLD! Will review later

- Query
  - The client's adress (safebooru) adress is HTTPS, valid and reachable

  - Test that all arguments do what they're supposed to
  - -P + -j
  - -P and not -j
  - no -P and no -j, no args

  - Ensure duplicate queries are not done more than once
  - Ensure duplicate posts are removed from output, test query: "1 id:1"
  - Test merged_output() with 5 queries:
    MD5, ID, post URL, result URL and search queries
  - Try to exceed Danbooru's page limit for non-members (1000 with limit 20?)
  - Try to search for too many tags (>2)

  - Verify duplicate pages are removed (test with -p 3 2-4)
  - Test <nbr>+ and +<nbr> page args
  - Verify the correct number of posts to get are reported in those two cases:
    `min(len(page_set) * params["limit"], post_total)`

- Download
  - Load compressed JSON from stdin
  - Load pretty-printed JSON from file
  - Load python list of dicts (query's output)

  - Trying to DL post without ID
  - Trying to DL post without URL
  - Trying to DL post with wrong MD5
  - Trying to DL post with invalid file URL

  - Normal DL with an ugoira
  - Normal DL with <process number> non-ugoira posts
    - Ensure their estimated size is exact
  - Ensure estimated size string ends with " max" only if ugoiras are present

- Utils
  - CTRL-C doesn't show traceback (wait 1s at least)
  - "Usage:" is capitalized in script's helps
  - bytes2human report correct sizes for all units
  - get_file_md5 with chunkSize of 1kB reports correct md5 for a 2KB file
