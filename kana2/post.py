"""Post class."""

import logging as log
import os

import arrow
import whratio
from orderedset import OrderedSet

from . import client, io, utils

RESOURCES      = OrderedSet(("info", "extra", "artcom", "notes", "media"))
RESOURCES_JSON = RESOURCES - set(("media",))


class Post(object):
    def __init__(self, query=None,
                 info=None, extra=None, artcom=None, notes=None, media=None,
                 _client = client.DEFAULT, _blank_line=True):
        self.info    = info
        self.extra   = extra
        self.artcom  = artcom
        self.notes   = notes
        self.media   = media

        self._client     = _client
        self._blank_line = _blank_line

        if query:
            self.info = next(self._client.info_auto(query))
        elif not self.info:
            raise TypeError("No query or info parameter was passed.")

        self.id = self.info["id"]

        # User can't pass self keys as init args, use set_paths().
        self.paths = None
        self.set_paths()

        if self._blank_line:
            utils.blank_line()

    # Magic methods:

    def __repr__(self):
        return f"Post(id={self.id})"

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other_post):
        for res in ("id", *RESOURCES):
            if getattr(self, res) != getattr(other_post, res):
                return False
        return True

    def __copy__(self):
        return Post(None, self.info, self.extra, self.artcom, self.notes,
                    self.media, self._client, self._blank_line)

    # Resource retrieval:

    def _log_retrieving(self, resource, doing="Retrieving"):
        log.info(f"{doing} {resource} for post {self.id}...")


    def _empty_result_to_none(self, resource, result_list):
        if not result_list or result_list == []:
            log.info(f"No {resource} found for post {self.id}.")
            setattr(self, resource, None)


    def get_all(self, overwrite=False, excludes=()):
        for res in RESOURCES - set(("info",)):
            if (not getattr(self, res) or overwrite) and res not in excludes:
                getattr(self, f"get_{res}")()

        utils.blank_line()
        return self


    def get_extra(self):
        # pylint: disable=unused-variable
        self._log_retrieving("extra info", "Generating")

        w_h         = (self.info["image_width"], self.info["image_height"])
        ratio_int   = whratio.ratio_int(*w_h)
        ratio_float = whratio.ratio_float(*w_h)
        fetch_date  = arrow.now()

        is_broken = False

        if "file_ext" not in self.info:
            log.warning(f"Can't get extra media info for post {self.id}.")
            is_broken = True

        elif self.info["file_ext"] != "zip":
            is_ugoira = False
            dl_url    = self.info["file_url"]
            dl_ext    = self.info["file_ext"]
            dl_size   = self.info["file_size"]

        else:
            is_ugoira = True
            dl_url    = self.info["large_file_url"]  # webm URL
            dl_ext    = dl_url.split(".")[-1]
            dl_size   = int(self._client
                            .http("head", dl_url)
                            .headers["content-length"])

        self.extra, defineds = {}, locals()

        for key in ("ratio_int", "ratio_float", "fetch_date",
                    "is_broken", "is_ugoira", "dl_url", "dl_ext", "dl_size"):
            self.extra[key] = defineds.get(key, None)

        return self


    def get_artcom(self):
        # Post should have an artcom if it has commentary(_request) tag.
        meta_tags   = f" {self.info['tag_string_meta']} "
        has_com_tag = " commentary "         in meta_tags or \
                      " commentary_request " in meta_tags

        # Post created in the last 24 hours may have not been
        # processed yet to have the commentary(_request) tags.
        created_in_last_24h = arrow.get(self.info["created_at"]) >= \
                              arrow.now().shift(hours=-24)

        if created_in_last_24h and not has_com_tag:
            self._log_retrieving("potential artist commentary")

        elif has_com_tag:
            self._log_retrieving("artist commentary")

        if has_com_tag or created_in_last_24h:
            self.artcom = self._client.api("artist_commentary_list",
                                           post_id=self.info["id"])

        self._empty_result_to_none("artcom", self.artcom)
        return True if self.artcom else False


    def get_notes(self):
        # If last_noted_at doesn't exist or is null, the post has no notes.
        if self.info.get("last_noted_at"):
            self._log_retrieving("notes")
            self.notes = self._client.api("note_list", post_id=self.id)

        self._empty_result_to_none("notes", self.notes)
        return True if self.notes else False


    def get_media(self, chunk_size=8 * 1024 ** 2):  # 8M
        if not self.extra:
            self.get_extra()

        if self.extra["is_broken"]:
            log.warning(f"Can't get media for broken post {self.id}.")
            return False

        self._log_retrieving("media generator (%s, %s)" % (
            self.extra["dl_ext"],
            utils.bytes2human(self.extra["dl_size"]) \
            if self.extra["dl_size"] else "Unknown size"))

        response = self._client.http("get", self.extra["dl_url"], stream=True)
        if not response:
            return False

        self.media = response.iter_content(chunk_size)
        return True

    # I/O:

    def set_paths(self, **user_paths):
        self.paths = {}

        for res in RESOURCES:
            if res in user_paths:  # Passed in kwargs
                self.paths[res] = utils.expand_path(user_paths[res])

            # Was set by the above if, or already set by a previous set_paths()
            if self.paths.get(res) is not None:
                continue

            ext = None
            # Set a default value, i.e. <id>/<resource>.<ext>
            if res in RESOURCES_JSON:
                ext = "json"

            elif res == "media":
                if not self.extra:
                    self.get_extra()
                ext = self.extra["dl_ext"]

            else:
                log.warning(f"Can't determine media ext for post {self.id}.")

            self.paths[res] = (f"{self._client.name}-{self.id}"
                               f"{os.sep}{res}.{ext}")
        return self


    def write(self, overwrite=False):
        for res in RESOURCES:
            # Not fetched or user specified False as path:
            if not getattr(self, res) or self.paths[res] is False:
                continue

            if res in RESOURCES_JSON:
                action  = "Writing"  # Got the actual data, not a generator.
                content = utils.jsonify(getattr(self, res))
                mode    = "w"
                chunk   = False

            elif res == "media":
                action  = "Downloading"  # Since it's a lazy generator.
                content = getattr(self, res)
                mode    = "wb"
                chunk   = True

            path  = self.paths[res]
            msg   = f"{action} {res} to '{path}' for post {self.id}..."
            wrote = io.write(content, path, mode, msg, chunk, overwrite)

            if res == "media" and wrote:
                self.verify_media()
                # Get a new media generator, since the current one was emptied.
                self.get_media()

        utils.blank_line()
        return self


    def verify_media(self):
        def log_verifying():
            log.info(f"{use} media verification for post {self.id}...")

        def log_failed():
            log.warning(f"{use} verification for post {self.id} failed!"
                        f"Expected {expected}, got {actual}.")

        if not os.path.exists(self.paths["media"]):
            log.warning(f"File {self.paths['media']} doesn't exist, "
                        f"can't verify media.")
            return False

        if not self.extra["is_ugoira"]:
            use      = "MD5"
            log_verifying()
            expected = self.info["md5"]
            actual   = io.get_file_md5(self.paths["media"])
        elif self.extra["dl_size"]:
            use      = "File size"
            log_verifying()
            expected = self.extra["dl_size"]
            actual   = os.path.getsize(self.paths["media"])
        else:
            log.warning(f"No MD5 or dl_size to verify post {self.id} media.")
            return False

        if expected == actual:
            return True

        log_failed()
        return False
