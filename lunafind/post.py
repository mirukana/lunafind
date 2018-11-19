# Copyright 2018 miruka
# This file is part of lunafind, licensed under LGPLv3.

import os
from pathlib import Path
from typing import Optional, Union

import pendulum as pend
from atomicfile import AtomicFile
from cached_property import cached_property

# pylint: disable=no-name-in-module
from fastnumbers import fast_int

from . import LOG, utils
from .clients import auto, base, local


class GotNoPostInfoError(Exception):
    pass


class Post:
    def __init__(self,
                 id_or_url: Union[None, int, str]   = None,
                 info:      Optional[base.InfoType] = None,
                 client:    Optional[base.Client]   = None
                ) -> None:
        assert id_or_url or info

        self.client = auto.get(client)

        if info:
            self.info = info

        elif isinstance(id_or_url, int):
            self.info = self.client.info_id(id_or_url)

        elif isinstance(id_or_url, (str, Path)):
            id_or_url   = id_or_url.strip()
            self.client = auto.get(id_or_url)
            self.info   = next(self.client.info_location(id_or_url))

        else:
            raise TypeError("id_or_url: must be int post ID or str URL.")

        if not self.info:
            raise GotNoPostInfoError(f"Got no info for post {id_or_url!r}.")

        if isinstance(info, local.IndexedInfo):
            return

        if "fetched_from" not in self.info:
            self.info["fetched_from"] = self.client.name

        if "fetched_at" not in self.info:
            self.info["fetched_at"] = pend.now()\
                                      .format(self.client.date_format)


    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, title='{self.title}')"


    def get_location(self, resource: str = "post", absolute: bool = False
                    ) -> str:
        return self.client.get_location(self.info, resource, absolute=absolute)


    @cached_property
    def title(self) -> str:
        kinds = {k: utils.join_comma_and(*self.info[f"tag_string_{k}"].split())
                 for k in ("character", "copyright", "artist")}

        return ("{character} ({copyright}) drawn by {artist}%".format(**kinds)
                .replace("() drawn by", "drawn by")
                .replace("drawn by %", "")
                .replace("%", "")
                .strip()
                or "untitled")

    @cached_property
    def id(self) -> int:
        return fast_int(self.info["id"])

    @cached_property
    def artcom(self) -> base.ArtcomType:
        return self.client.artcom(self.info)

    @cached_property
    def media(self) -> base.MediaType:
        return self.client.media(self.info)

    @cached_property
    def notes(self) -> base.NotesType:
        return self.client.notes(self.info)


    def write(self,
              base_dir:  Union[str, Path] = Path("."),
              overwrite: bool             = False,
              warn:      bool             = True) -> None:

        if isinstance(self.client, local.Local):
            return

        post_dir = Path(base_dir) / "{fetched_from}-{id}".format(**self.info)
        post_dir.mkdir(parents=True, exist_ok=True)

        for res in ("info", "artcom", "notes", "media"):
            if res == "media" and "file_ext" not in self.info:
                LOG.warning("No decensor data found for post %d, "
                            "can't download media.", self.info["id"])
                continue

            ext = "json" if res != "media" else self.info["file_ext"]
            ext = "webm" if ext == "zip"   else ext

            path = post_dir / f"{res}.{ext}"

            if path.exists() and not overwrite:
                if warn:
                    LOG.warning("Not overwriting %r", str(path))
                continue

            content = getattr(self, res)

            if not content:
                continue

            if res != "media":
                with AtomicFile(path, "w") as out:
                    out.write("%s%s" %
                              (utils.jsonify(content).rstrip(), os.linesep))
                continue

            if self.info["file_ext"] != "zip":
                LOG.info("Downloading %s of %s for post %d",
                         self.info["file_ext"].upper(),
                         utils.bytes2human(self.info["file_size"]),
                         self.info["id"])
            else:
                LOG.info("Downloading WebM ugoira for post %d",
                         self.info["id"])

            with AtomicFile(path, "wb") as out:
                for chunk in content:  # pylint: disable=not-an-iterable
                    out.write(chunk)
