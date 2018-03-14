# Notes

## Install dependencies

(Pybooru with the latest improvements isn't released yet on pip.)

    sudo pip3 install https://git.io/vNT0B requests halo arrow --upgrade

## kanarip v1 incompatibilities

- Save JSONS in info/ instead of generating tags/ and meta/
- Downloaded artcom and notes will no longer be wrapped in lists
- Download full artcom and notes

## TODO

- Update to Pybooru new version

- DL script
    - Do not overwrite files by default?

- CLI script
    - [termcolor](https://pypi.python.org/pypi/termcolor), used in **halo**
    - zplug-like UI for multiprocess downloading?
    - Use [doctopt](https://docopt.readthedocs.io/en/latest/)
    - Config system

- Check for booru return code not just in media

- Ignore and error lists

- Filter script
    - Duplicates
    - Blacklist
    - Tag conditions
    - "JSON" conditions
    - Sort by specific key, ascending or descending
    - Max number of posts

- Thumbnail script

- Generate docs and manpages with Sphinx

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
