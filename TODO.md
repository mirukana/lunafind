# lunakit TODO and idea list

## Minor

- Make `-k` show keys of the resource printed with `-R`
- Option to show local `-R` resource path
- `--order`
- Don't return a Python-converted thing when using `-k`

- Flag file or dir name modification to prevent
  updates/remember deleted posts and not refetch them/force recaching/etc

- Fuzzy tag filtering

- Stop upon reaching pagination limit or too many timeouts

- Intelligent post update based on `updated_at` and `fetched_at` keys,
  Allow updating + writing local post using remote booru

- Max limit client attr (also use in lunasync)
- Implement all set operators for attridict
- Order: artcomm and custom

## Major

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
