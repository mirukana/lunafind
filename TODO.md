# lunafind TODO and idea list

## Minor

- Fix filter, deleted keys:
      "title", "booru", "booru_url", "post_url", "children_num", "mpixels",
      "ratio_int", "ratio_float", "is_broken", "is_ugoira"
      "dl_url", "dl_ext", "dl_size"

- Fix index corruption
- Fix limit 1 reporting two posts

- Flag file or dir name modification to prevent
  updates/remember deleted posts and not refetch them/force recaching/etc

- Some way to view auto-filtered posts

- Stop upon reaching pagination limit or too many timeouts

- Intelligent post update based on `updated_at` and `fetched_at` keys,
  Allow updating + writing local post using remote booru

- Max limit client attr (also use in lunasync)
- Implement all set operators for attridict
- Order: artcomm and custom

## Major

- Support multi-booru + local mixed searches
- Clean up the filtering.py code
- Tag aliases for filtering
- Filter: Danbooru hard stuff that needs users/etc info
- Integrate Decensooru?

- Transparently store user resource modifications in separate (patch?) files

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
- Find posts missing media that aren't marked as broken
