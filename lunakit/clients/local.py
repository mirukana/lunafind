# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import collections
import csv
import gzip
import math
import os
from pathlib import Path
from random import randint
from typing import Generator, Iterable, Optional, Union

import simplejson
from dataclasses import dataclass, field

from . import base
from .. import LOG
from ..filtering import filter_all
from .base import InfoType

POST_FIELDS = (
    "children_ids",
    "created_at",
    "fav_count",
    "fetched_at",
    "fetched_from",
    "file_ext",
    "file_size",
    "id",
    "image_height",
    "image_width",
    "is_deleted",
    "is_flagged",
    "is_note_locked",
    "is_pending",
    "is_rating_locked",
    "is_status_locked",
    "last_comment_bumped_at",
    "last_commented_at",
    "last_noted_at",
    "md5",
    "parent_id",
    "rating",
    "score",
    "source",
    "tag_string",
    "tag_string_artist",
    "tag_string_character",
    "tag_string_copyright",
    "tag_string_general",
    "tag_string_meta",
    "updated_at",
    "uploader_name",
)

def _indexedpost_getitem(self, key):
    if isinstance(key, str):
        return getattr(self, key)
    return tuple(self)[key]

IndexedPost             = collections.namedtuple("IndexedPost", POST_FIELDS)
IndexedPost.__getitem__ = _indexedpost_getitem


@dataclass
class Local(base.Client):
    name: str              = "local"
    path: Union[Path, str] = Path(".")

    index: Path = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self.path  = Path(self.path or ".").expanduser()
        self.index = self.path / "index.tsv.gz"


    def _index_add(self, post_dirnames: Iterable[str]) -> base.InfoGenType:
        LOG.info("Indexing %d posts...", len(post_dirnames))

        with gzip.open(self.index, "at+", newline="") as file:
            writer = csv.DictWriter(
                file,
                delimiter    = "\t",
                fieldnames   = POST_FIELDS,
                extrasaction = "ignore"
            )

            for post in post_dirnames:
                try:
                    info = simplejson.load(
                        open(f"{post}{os.sep}info.json", "r")
                    )
                except (FileNotFoundError, NotADirectoryError) as err:
                    if not str(err.filename).startswith(self.index.name):
                        LOG.error(str(err))
                    continue

                writer.writerow(info)
                yield info


    def _index_iter(self, post_dirnames: Iterable[str]
                   ) -> Generator[IndexedPost, None, None]:

        post_dirnames = set(post_dirnames)
        post_dirnames.discard(self.index.name)

        if not self.index.exists():
            yield from self._index_add(post_dirnames)
            return

        lines_to_del = []

        with gzip.open(self.index, "rt+", newline="") as file:
            reader = csv.reader(file, delimiter="\t")

            for i, row in enumerate(reader, 1):
                row = (True if i == "True" else False if i == "False" else i
                       for i in row)
                ip  = IndexedPost(*row)
                key = f"{ip.fetched_from}-{ip.id}"

                try:
                    post_dirnames.remove(key)
                except KeyError:
                    lines_to_del.append(i)
                else:
                    yield ip

        if post_dirnames:
            yield from self._index_add(post_dirnames)

        if lines_to_del:
            self._index_del(*lines_to_del)


    def _index_del(self, *line_nums: int) -> None:
        LOG.info("%d post dirs gone, deleting from index...", len(line_nums))

        tmp_file = self.index.parent / f".{self.index.name}"

        with gzip.open(self.index, "rt", newline="") as in_file, \
             gzip.open(tmp_file,   "wt", newline="") as out_file:

            for i, line in enumerate(in_file, 1):
                if i not in line_nums:
                    out_file.write(line)

        tmp_file.rename(self.index)


    def _get_post_path(self, info: InfoType) -> Path:
        return self.path / f"{info['fetched_from']}-{info['id']}"


    def _read_res(self, info: InfoType, file: str, binary: bool = False
                 ) -> Union[str, bytes, None]:

        path = self._get_post_path(info)

        try:
            path /= file
        except FileNotFoundError:
            return None

        return path.read_text() if not binary else path.read_bytes()


    def _read_json(self, info: InfoType, file_noext: str) -> Optional[str]:
        res = self._read_res(info, f"{file_noext}.json")
        if res is None:
            return None
        return simplejson.loads(res)


    def info_booru_id(self, booru: str, post_id: int) -> InfoType:
        fake_info = {"fetched_from": booru, "id": post_id}
        return self._read_json(fake_info, "info.json")


    def info_search(self,
                    tags:   str           = "",
                    pages:  base.PageType = 1,
                    limit:  Optional[int] = None,
                    random: bool          = False,
                    raw:    bool          = False) -> base.InfoGenType:

        def sort_func(dirname):
            if random:
                return randint(1, 1_000_000)
            try:
                return int(dirname.split("-")[-1])
            except ValueError:
                return -1

        posts = os.listdir(self.path)
        posts.sort(key=sort_func, reverse=True)

        ok_i  = max_i = None

        if limit and limit != -1:
            last  = math.ceil(len(posts) / limit)
            ok_i  = {i
                     for p in self._parse_pages(pages, last)
                     for i in range((p - 1) * limit, (p - 1) * limit + limit)}
            max_i = sorted(ok_i)[-1]

        filter_gen = filter_all(self._index_iter(posts), terms=tags, raw=raw)
        del posts

        for i, post in enumerate(filter_gen):
            if max_i and i > max_i:
                break

            if ok_i and i not in ok_i:
                continue

            yield post


    def artcom(self, info: InfoType) -> base.ArtcomType:
        return self._read_json(info, "artcom") or []


    def media(self, info: InfoType) -> base.MediaType:
        ext = "webm" if info["file_ext"] == "zip" else info["file_ext"]
        return self._read_res(info, f"media.{ext}", binary=True)


    def notes(self, info: InfoType) -> base.NotesType:
        return self._read_json(info, "notes") or []


    def count_posts(self, tags: str = "") -> int:
        return len(list(self.info_search(tags)))


    def get_url(self, info: base.InfoType, resource: str = "post") -> str:
        def verify(path: Path) -> Optional[str]:
            if path.exists():
                return str(path)
            return None

        assert resource in ("post", "artcom", "info", "media", "notes")
        path = self._get_post_path(info).resolve()

        if resource == "post":
            return verify(path)

        if resource == "media":
            ext = "webm" if info["file_ext"] == "zip" else info["file_ext"]
            return verify(path / f"media.{ext}")

        return verify(path / f"{resource}.json")
