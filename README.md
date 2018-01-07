# Notes

## Install dependencies

(Pybooru with the latest improvements isn't released yet on pip.)

    sudo pip3 install https://git.io/vNT0B requests halo --upgrade

## kanarip v1 compatibility

- Save JSONS instead of tag files
- Downloaded artcom and notes will no longer be wrapped in lists
- Download full artcom and notes

## TODO

→ Proper dir structure, example:

    ```
    kana2/
        README.md
        setup.py
        kana2/
            __init__.py
            download/
                ...
            filter/
                ...
            query/
                ...
    ```

- Break query's page function stuff into smaller functions

- (ignore me)
- Subcommand design, e.g. `kana2 q|query|d|download|f|filter args...`
- Use [doctopt](https://docopt.readthedocs.io/en/latest/) instead of argparser
- Config system
- Better CLI interface, progress bar for dl, e'#tc
- [termcolor](https://pypi.python.org/pypi/termcolor), used in **halo**

- Query script
  - Multiprocess
  - Patch pybooru.\_request to handle errors ourself
  - Allow page/limit/etc to modify a single request

- Download script
  - Artist commentaries JSON
  - Notes JSON
  - zplug-like UI for multiprocess downloading
  - Global timer, so that 0.5-1s must have passed between any request
  - Do not overwrite files by default?
  - Option to define what types of files will be downloaded (media/info/etc),
    defaults to all (m,i,a,n)
  - Option to disable adding download time, <progName> prefix for added key

- Ignore and error lists

- Filter script
  - Duplicates
  - Blacklist
  - Tag conditions
  - "JSON" conditions
  - Sort by specific key, ascending or descending
  - Max number of posts

- Docstrings
  - Adapt krip manpages or use docstrings to generate stuff

- Read [ŧhis](https://wiki.python.org/moin/PythonSpeed/PerformanceTip) and
  apply whatever can be learned from it

## Tests to write

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
