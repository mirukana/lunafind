# lunakit TODO and idea list

## Minor

- Logger non-global object
- Don't update post dirs with a *READONLY* file inside
- Max limit client attr (also use in lunasync)
- Implement all set operators for attridict
- Order: artcomm and custom

## Major

- Downloader class that takes in iterable (Stream or `iter(Album.list)`),
  able to keep track and resume downloads, even in CLI usage (file save?)

- Tag aliases for filtering
- Filter: Danbooru hard stuff that needs users/etc info
- Integrate Decensooru?

- Local clients to manage written to disk posts
- Transparently store user resource modifications in separate patch files

## Etc

- Document filter and info differences from Danbooru
- Docstrings, documentation
- Tests

## Programs

- bash/zsh completitions
- zplug/emerge-like monitor for downloads

- Tag subs management with already fetched list
- Tag aliases and relations
- Create Post from a non-booru image using IQDB
