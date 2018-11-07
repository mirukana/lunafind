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
from dataclasses import dataclass

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


    def __post_init__(self) -> None:
        self.path = Path(self.path).expanduser()


    @staticmethod
    def _create_index(post_dirnames: Iterable[str]) -> None:
        LOG.info("Indexing %d posts...", len(post_dirnames))

        with gzip.open("index.tsv.gz", "at", newline="") as file:
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
                    if err.args[0] != "index.tsv.gz":
                        LOG.error(str(err))

                writer.writerow(info)

        LOG.info("Index updated.")


    @staticmethod
    def _iter_index() -> Generator[IndexedPost, None, None]:
        with gzip.open("index.tsv.gz", "rt", newline="") as file:
            reader = csv.reader(file, delimiter="\t")
            for row in reader:
                row = (True if i == "True" else False if i == "False" else i
                       for i in row)
                yield IndexedPost(*row)


    def _read_res(self, info: InfoType, file: str, binary: bool = False
                 ) -> Union[str, bytes, None]:

        path = self.path / "{}-{}".format(info["fetched_from"], info["id"])

        try:
            path = (path / file) if "*" not in file else next(path.glob(file))
            return path.read_text() if not binary else path.read_bytes()

        except (StopIteration, FileNotFoundError):
            return None


    def _read_json(self, info: InfoType, file: str) -> Optional[str]:
        res = self._read_res(info, file)
        if res is None:
            return None
        return simplejson.loads(self._read_res(info, file))


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

        if not (self.path / "index.tsv.gz").exists():
            self._create_index(posts)

        ok_i  = max_i = None

        if limit:
            last  = math.ceil(len(posts) / limit)
            ok_i  = {i
                     for p in self._parse_pages(pages, last)
                     for i in range((p - 1) * limit, (p - 1) * limit + limit)}
            max_i = sorted(ok_i)[-1]

        filter_gen = filter_all(self._iter_index(), terms=tags, raw=raw)

        for i, post in enumerate(filter_gen):
            if max_i and i > max_i:
                break

            if ok_i and i not in ok_i:
                continue

            yield post


    def artcom(self, info: InfoType) -> base.ArtcomType:
        return self._read_json(info, "artcom.json") or []


    def media(self, info: InfoType) -> base.MediaType:
        return self._read_res(info, "media.*", binary=True)


    def notes(self, info: InfoType) -> base.NotesType:
        return self._read_json(info, "notes.json") or []


    def count_posts(self, tags: str = "") -> int:
        return len(list(self.info_search(tags)))
