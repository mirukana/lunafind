"""Post class."""

import logging as log
import os
import pprint

import arrow
import attr
import whratio

from . import CHUNK_SIZE, CLIENT, net, utils

RESOURCES_JSON  = set(("info", "extra", "artcom", "notes"))
RESOURCES       = RESOURCES_JSON | set(("media",))


@attr.s
class Post(object):
    info  = attr.ib(repr=False)
    extra = media = artcom = notes = attr.ib(default=None, repr=False)

    init_get = attr.ib(default=True, repr=False, cmp=False)
    client   = attr.ib(default=CLIENT, repr=False, cmp=False)

    # User won't be able to use self keys before the object is initialized,
    # so set_paths() is the only way to change paths.
    paths = attr.ib(init=False, factory=dict, repr=False, cmp=False)
    id    = attr.ib(init=False)


    def __attrs_post_init__(self):
        self.id = self.info["id"]
        self.get_extra()
        self.set_paths()

        if self.init_get:
            # Do not overwrite user args; use the already fetched extra.
            self.get_all(overwrite=False, excludes="extra")


    def __str__(self):
        return pprint.pformat(self.__dict__)


    def _log_retrieving(self, resource, doing="Retrieving"):
        log.info(f"{doing} {resource} for post {self.id}...")


    def _log_writing(self, resource, out_path, doing="Writing"):
        log.info(f"{doing} {resource} to '{out_path}' for post {self.id}...")


    def _log_loading(self, resource, in_path, doing="Loading"):
        log.info(f"{doing} {resource} from '{in_path}' for post {self.id}...")


    def _log_verify_media(self, verify_type):
        log.info(f"Verifying media using {verify_type} for post {self.id}...")


    def _log_verify_media_fail(self, verify_type, expected, got):
        log.warning(f"{verify_type} media verification for post {self.id} "
                    f"failed! Expected {expected} bytes, got {got}.")


    def _has_extra(self, to_do):
        if not self.extra:
            log.warning(f"Extra informations required to {to_do} for "
                        f"post {self.id}.")
            return False
        return True


    def _empty_result_to_none(self, resource, result_list):
        if not result_list or result_list == []:
            log.info(f"No {resource} found for post {self.id}.")
            setattr(self, resource, None)


    def _validate_info(self, resource):
        required_keys = {
            "extra":  ("file_url", "large_file_url",
                       "image_width", "image_height"),
            "artcom": ("tag_string_meta", "created_at"),
            "notes":  ()
        }

        if utils.dict_has(self.info, *required_keys[resource]):
            return True

        log.warning(f"Post {self.id} is missing one of "
                    f"{required_keys[resource]} needed to get {resource}.")
        return False


    def set_paths(self, **user_paths):
        for res in RESOURCES:
            if res in user_paths:
                self.paths[res] = user_paths[res]

            # Was set by the above if, or already set by a previous set_paths()
            if self.paths.get(res) is not None:
                continue

            # Set a default value, i.e. <id>/<resource>.<ext>
            if res in RESOURCES_JSON:
                ext = "json"
            elif res == "media" and self.extra:
                ext = self.extra["dl_ext"]
            else:
                ext = None

            self.paths[res] = (f"{self.client.site_name}-{self.id}"
                               f"{os.sep}{res}.{ext}")


    def get_all(self, overwrite=True, excludes=()):
        for res in RESOURCES - set(("info",)):
            if (overwrite or not getattr(self, res)) and res not in excludes:
                getattr(self, f"get_{res}")()


    def get_extra(self):
        def manual_get_size(self, media_url):
            return int(net.http("head", media_url, self.client.client).headers[
                "content-length"])

        if not self._validate_info("extra"):
            return False

        self._log_retrieving("extra info", "Generating")

        url = self.info.get("file_url")
        ext = url.split(".")[-1]

        if ext != "zip":
            is_ugoira = False
            size      = self.info.get("file_size", manual_get_size(self, url))
        else:
            is_ugoira = True
            url       = self.info["large_file_url"]  # Video URL
            ext       = url.split(".")[-1]
            size      = manual_get_size(self, url)

        self.extra = {
            "dl_url":      url,
            "dl_ext":      ext,
            "dl_size":     size,
            "is_ugoira":   is_ugoira,
            "ratio_int":   whratio.ratio_int(self.info["image_width"],
                                             self.info["image_height"]),
            "ratio_float": whratio.ratio_float(self.info["image_width"],
                                               self.info["image_height"]),
            "fetch_date":  arrow.now().format("YYYY-MM-DDTHH:mm:ss.SSSZZ")
        }

        return True


    def get_media(self, chunk_size=CHUNK_SIZE):
        if not self._has_extra("verify media"):
            return False

        self._log_retrieving("media generator (%s, %s)" % (
            self.extra["dl_ext"],
            utils.bytes2human(self.extra["dl_size"])))

        self.media = net.http("get", self.extra["dl_url"], self.client.client,
                              stream=True).iter_content(chunk_size)

        return True


    def get_artcom(self):
        if not self._validate_info("artcom"):
            return False

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
            self.artcom = net.booru_api(self.client.artist_commentary_list,
                                        post_id=self.info["id"])

        self._empty_result_to_none("artcom", self.artcom)

        return True


    def get_notes(self):
        if not self._validate_info("notes"):
            return False

        # If last_noted_at doesn't exist or is null, the post has no notes.
        if self.info.get("last_noted_at"):
            self._log_retrieving("notes")
            self.notes = net.booru_api(self.client.note_list, post_id=self.id)

        self._empty_result_to_none("notes", self.notes)

        return True


    def write(self, overwrite=False):
        for res in RESOURCES:
            # Skip if this resource hasn't been fetched;
            # or the user specified False as path.
            if not getattr(self, res) or self.paths[res] is False:
                continue

            function = utils.write
            content  = getattr(self, res)
            out_path = self.paths.get(res, self.paths[res])
            mode     = "w"

            if res == "media":
                log_action = "Downloading"  # Since it's a lazy generator
                function   = utils.write_chunk
                mode       = "wb"

            if res in RESOURCES_JSON:
                log_action = "Writing"  # Got the actual data, not a generator.
                content    = utils.jsonify(getattr(self, res)) \

            self._log_writing(res, out_path, doing=log_action)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            function(content, out_path, mode, overwrite)

            if res == "media":
                self.verify_media()
                # Get a new media generator, since the current one was emptied.
                self.get_media()

    def load(self, overwrite=True):
        raise NotImplementedError("Need to write post from disk/id/etc loader")

        # for res in RESOURCES:
            # can_write = overwrite or not getattr(self, res)

            # if can_write and self.paths[res] is not False:
                # in_path = self.paths[res]
                # mode    = "rb" if res in RESOURCES_MEDIA else "r"

                # self._log_loading(res, in_path)
                # setattr(self, res, utils.load_file(in_path, mode))


    def verify_media(self):
        if not self._has_extra("verify media"):
            return False

        if "md5" in self.info and not self.extra["is_ugoira"]:
            return self.verify_media_by_md5()

        return self.verify_media_by_filesize()


    def verify_media_by_md5(self):
        self._log_verify_media("MD5")
        expected = self.info.get("md5")
        actual   = utils.get_file_md5(self.paths["media"])

        if expected != actual:
            self._log_verify_media_fail("MD5", expected, actual)
            return False

        return True


    def verify_media_by_filesize(self):
        self._log_verify_media("file size")
        expected = self.extra["dl_size"]
        actual   = os.path.getsize(self.paths["media"])

        if expected != actual:
            self._log_verify_media_fail("File size", expected, actual)
            return False

        return True
