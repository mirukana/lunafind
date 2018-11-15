# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import collections
import csv
import math
import multiprocessing as mp
import os
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Callable, Generator, List, Optional, Sequence, Union

import simplejson
from atomicfile import AtomicFile
from dataclasses import dataclass, field

# pylint: disable=no-name-in-module
from fastnumbers import fast_int

from . import base
from .. import LOG, order
from ..filtering import filter_all
from .base import InfoType


def str2bool(string: str) -> Union[bool, str, None]:
    return True  if string == "True"  else \
           False if string == "False" else \
           None  if not string        else string


def str2int(string: str) -> Optional[int]:
    return fast_int(string, None)


POST_FIELDS = collections.OrderedDict({
    # Starting keys to sort rows if needed
    "id":           str2int,
    "fetched_from": str,
    "fetched_at":   str,

    # Other keys useful for filtering
    "children_ids":           str,
    "created_at":             str,
    "fav_count":              str2int,
    "file_ext":               str,
    "file_size":              str2int,
    "image_height":           str2int,
    "image_width":            str2int,
    "is_deleted":             str2bool,
    "is_flagged":             str2bool,
    "is_note_locked":         str2bool,
    "is_pending":             str2bool,
    "is_rating_locked":       str2bool,
    "is_status_locked":       str2bool,
    "last_comment_bumped_at": str,
    "last_commented_at":      str,
    "last_noted_at":          str,
    "md5":                    str,
    "parent_id":              str2int,
    "rating":                 str,
    "score":                  str2int,
    "source":                 str,
    "tag_string":             str,
    "tag_string_artist":      str,
    "tag_string_character":   str,
    "tag_string_copyright":   str,
    "tag_string_general":     str,
    "tag_string_meta":        str,
    "updated_at":             str,
    "uploader_name":          str,

    # Keys not needed for filtering:
    "approver_id":          str2int,
    "bit_flags":            str2int,
    "down_score":           str2int,
    "file_url":             str,
    "has_active_children":  str2bool,
    "has_children":         str2bool,
    "has_large":            str2bool,
    "has_visible_children": str2bool,
    "is_banned":            str2bool,
    "is_favorited":         str2bool,
    "large_file_url":       str,
    "pixiv_id":             str2int,
    "pool_string":          str,
    "preview_file_url":     str,
    "tag_count":            str2int,
    "tag_count_artist":     str2int,
    "tag_count_character":  str2int,
    "tag_count_copyright":  str2int,
    "tag_count_general":    str2int,
    "tag_count_meta":       str2int,
    "up_score":             str2int,
    "uploader_id":          str2int,

    # Disabled for performance reasons
    # "keeper_data":             str2dict,
    # "pixiv_ugoira_frame_data": str2dict,
})


_INDEXED_INFO_NT = collections.namedtuple("IndexedInfo", POST_FIELDS.keys())

class IndexedInfo(_INDEXED_INFO_NT):
    _row_converts: List[Callable] = POST_FIELDS.values()


    @classmethod
    def from_csv(cls, row: Sequence[str]) -> "IndexedInfo":
        return cls(*(v if isinstance(v, str) else c(v)
                     for c, v in zip(cls._row_converts, row)))


    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key)
        return tuple(self)[key]


@dataclass
class Local(base.Client):
    name: str              = "local"
    path: Union[Path, str] = Path(".")

    index: Path = field(init=False, default=None, repr=False)


    def __post_init__(self) -> None:
        self.path  = Path(self.path or ".").expanduser()
        self.index = self.path / "index.tsv"


    def _get_info(self, post_dirname: str) ->  base.InfoType:
        path = self.path / post_dirname / "info.json"
        with open(path, "r") as file:
            return simplejson.loads(file.read())


    def _index_add(self, post_dirnames: List[str]) -> base.InfoGenType:
        LOG.info("Indexing %d posts...", len(post_dirnames))

        post_dirnames.sort(key     = lambda d: fast_int(d.split("-")[-1], -1),
                           reverse = True)

        if not self.index.exists():
            self.index.write_text("")

        with open      (self.index, "r", newline="") as in_file, \
             AtomicFile(self.index, "w")             as out_file:

            # Not just using csv.DictReader for performance reasons
            id_idx = list(POST_FIELDS.keys()).index("id")
            reader = csv.reader(in_file, delimiter="\t")

            src_row_writer = csv.writer(out_file, delimiter="\t")
            new_info_writer = csv.DictWriter(
                out_file,
                delimiter    = "\t",
                fieldnames   = POST_FIELDS.keys(),
                extrasaction = "ignore"
            )

            pool  = ThreadPool(mp.cpu_count() * 5)
            tasks = [pool.apply_async(self._get_info, (p,))
                     for p in post_dirnames]

            def info_gen():
                for task in tasks:
                    try:
                        yield task.get()
                    except (FileNotFoundError, NotADirectoryError) as err:
                        if str(err.filename) != self.index.name:
                            LOG.error(str(err))

            info_gen = info_gen()
            try:
                new_info = next(info_gen)
            except StopIteration:
                return

            no_more_to_add = False

            for source_row in reader:
                try:
                    src_id = fast_int(source_row[id_idx],raise_on_invalid=True)
                except ValueError:
                    LOG.error("Removing invalid row in index: %r", source_row)
                    continue

                while not no_more_to_add and new_info["id"] > src_id:
                    new_info_writer.writerow(new_info)
                    yield new_info

                    try:
                        new_info = next(info_gen)
                    except StopIteration:
                        no_more_to_add = True

                src_row_writer.writerow(source_row)

            if not no_more_to_add:
                new_info_writer.writerow(new_info)
                yield new_info

            for remaining_info in info_gen:
                new_info_writer.writerow(remaining_info)
                yield remaining_info


    def _index_del(self, *line_nums: int) -> None:
        LOG.info("Deleting from index %d post dirs...", len(line_nums))

        with open      (self.index, "r", newline="") as in_file, \
             AtomicFile(self.index, "w")             as out_file:

            for i, line in enumerate(in_file, 1):
                if i not in line_nums:
                    out_file.write(line)


    def _index_iter(self, post_dirnames: List[str]
                   ) -> Generator[IndexedInfo, None, None]:

        if not self.index.exists():
            yield from self._index_add(post_dirnames)
            return

        lines_to_del     = []
        unfound_dirnames = set(post_dirnames)
        unfound_dirnames.discard(self.index.name)
        del post_dirnames

        with open(self.index, "r", newline="") as file:
            reader = csv.reader(file, delimiter="\t")

            for i, row in enumerate(reader, 1):
                try:
                    info = IndexedInfo.from_csv(row)
                except TypeError:
                    LOG.error("Corrupted post in index on line %d, "
                              "will try to repair: %r", i, row)
                    lines_to_del.append(i)
                    continue

                key  = f"{info.fetched_from}-{info.id}"

                try:
                    unfound_dirnames.remove(key)
                except KeyError:
                    lines_to_del.append(i)
                else:
                    yield info

        if lines_to_del:
            self._index_del(*lines_to_del)

        if unfound_dirnames:
            yield from self._index_add(list(unfound_dirnames))


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


    def info_md5(self, md5: str) -> base.InfoGenType:
        yield from self.info_search(f"md5:{md5}")


    # pylint: disable=arguments-differ
    def info_search(self,
                    tags:         str           = "",
                    pages:        base.PageType = 1,
                    limit:        Optional[int] = None,
                    random:       bool          = False,
                    raw:          bool          = False,
                    partial_tags: bool          = False) -> base.InfoGenType:

        posts = os.listdir(self.path)

        ok_i = max_i = None

        if limit and limit not in (-1, math.inf):
            last  = math.ceil(len(posts) / limit)
            ok_i  = {i
                     for p in self._parse_pages(pages, last)
                     for i in range((p-1) * limit, (p-1) * limit + limit)}
            max_i = sorted(ok_i)[-1]

        posts = filter_all(self._index_iter(posts),
                           terms=tags, raw=raw, partial_tags=partial_tags)

        if random:
            LOG.warning("Requested random results, this can take some time...")
            posts = iter(order.sort(list(posts), by="random"))

        for i, post in enumerate(posts):
            if max_i and i > max_i:
                break

            if ok_i and i not in ok_i:
                continue

            yield post


    def artcom(self, info: InfoType) -> base.ArtcomType:
        return self._read_json(info, "artcom") or []


    def media(self, info: InfoType) -> base.MediaType:
        try:
            ext = "webm" if info["file_ext"] == "zip" else info["file_ext"]
        except KeyError:
            return None
        return self._read_res(info, f"media.{ext}", binary=True)


    def notes(self, info: InfoType) -> base.NotesType:
        return self._read_json(info, "notes") or []


    def count_posts(self, tags: str = "") -> int:
        return len(list(self.info_search(tags)))


    def get_url(self,
                info: base.InfoType,
                resource: str  = "post",
                absolute: bool = False) -> Optional[str]:

        def verify(path: Path) -> Optional[str]:
            if path.exists():
                return str(path)
            return None

        assert resource in ("post", "artcom", "info", "media", "notes")
        path = self._get_post_path(info)

        if absolute:
            path = path.resolve()

        if resource == "post":
            return verify(path)

        if resource == "media":
            try:
                ext = "webm" if info["file_ext"] == "zip" else info["file_ext"]
            except KeyError:
                return None

            return verify(path / f"media.{ext}")

        return verify(path / f"{resource}.json")
