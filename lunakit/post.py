# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

import os
from pathlib import Path
from typing import Optional, Union

import pendulum as pend
from atomicfile import AtomicFile
from cached_property import cached_property

from . import LOG, utils
from .clients import base, local, net


class Post:
    def __init__(self,
                 id_or_url: Union[None, int, str]   = None,
                 info:      Optional[base.InfoType] = None,
                 prefer:    Optional[base.Client]   = None
                ) -> None:
        assert id_or_url or info

        self.client = prefer or net.DEFAULT

        if info:
            self.info = info

        elif isinstance(id_or_url, int):
            self.info = self.client.info_id(id_or_url)

        elif isinstance(id_or_url, str):
            id_or_url   = id_or_url.strip()
            self.client = net.client_from_url(id_or_url)
            self.info   = next(self.client.info_url(id_or_url))

        else:
            raise TypeError("id_or_url: must be int post ID or str URL.")

        if isinstance(info, local.IndexedPost):
            return

        if "fetched_from" not in self.info:
            self.info["fetched_from"] = self.client.name

        if "fetched_at" not in self.info:
            self.info["fetched_at"] = pend.now()\
                                      .format(self.client.date_format)


    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}, title='{self.title}')"


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
        return int(self.info["id"])

    @cached_property
    def url(self) -> str:
        if self.info["fetched_from"] == "local":
            return None

        client = net.ALIVE[self.info["fetched_from"]]
        return "%s%s" % (client.site_url,
                         client.post_url_template.format(**self.info))


    @cached_property
    def artcom(self) -> base.ArtcomType:
        return self.client.artcom(self.info)

    @cached_property
    def media(self) -> base.MediaType:
        return self.client.media(self.info)

    @cached_property
    def notes(self) -> base.NotesType:
        return self.client.notes(self.info)


    def write(self, overwrite: bool = False, warn: bool = True) -> None:
        if isinstance(self.client, local.Local):
            return

        post_dir = Path("{fetched_from}-{id}".format(**self.info))
        post_dir.mkdir(parents=True, exist_ok=True)

        for res in ("info", "artcom", "notes", "media"):
            if res == "media" and "file_ext" not in self.info:
                LOG.warning("No media available for post %d.", self.info["id"])
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
