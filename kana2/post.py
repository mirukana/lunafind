"""Post class"""
import logging

import arrow
import attr
import whratio

from . import CLIENT, net, utils


# TODO: Validation, see other attr possibilities
@attr.s
class Post(object):
    info     = attr.ib(repr=False)
    extra    = media = artcom = notes = attr.ib(default=None, repr=False)
    init_get = attr.ib(default=True, repr=False, cmp=False)
    client   = attr.ib(default=CLIENT, repr=False, cmp=False)
    id       = attr.ib(init=False)


    def __attrs_post_init__(self):
        self.id = self.info["id"]
        if self.init_get:
            self.get_all(overwrite=False)  # Do not overwrite user args


    def _log_retrieving(self, thing, verb="Retrieving"):
        logging.info(f"{verb} {thing} for post {self.id}...")


    def _empty_result_to_none(self, resource, result_list):
        if not result_list or result_list == []:
            logging.info(f"No {resource} found for post {self.id}.")
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

        logging.warning(f"Post {self.id} is missing one of "
                        f"{required_keys[resource]} needed to get {resource}.")
        return False


    def get_all(self, overwrite=True):
        for resource in ("extra", "media", "artcom", "notes"):
            if overwrite or not getattr(self, resource):
                getattr(self, f"get_{resource}")()


    def get_extra(self):
        def manual_get_size(self, media_url):
            return net.http("head", media_url, self.client.client).headers[
                "content-length"]

        if not self._validate_info("extra"):
            return

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


    def get_media(self, chunk_size=16 * 1024 ** 2):  # chunk_size of 16M
        if not self.extra:
            logging.warning(f"Extra informations required to get media for "
                            f"post {self.id}")
            return

        self._log_retrieving("media (%s, %s)" % (
            self.extra["dl_ext"],
            utils.bytes2human(self.extra["dl_size"])))

        self.media = net.http("get", self.extra["dl_url"], self.client.client,
                              stream=True).iter_content(chunk_size)


    def get_artcom(self):
        if not self._validate_info("artcom"):
            return

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


    def get_notes(self):
        if not self._validate_info("notes"):
            return

        # If last_noted_at doesn't exist or is null, the post has no notes.
        if self.info.get("last_noted_at"):
            self._log_retrieving("notes")
            self.notes = net.booru_api(self.client.note_list, post_id=self.id)

        self._empty_result_to_none("notes", self.notes)

    # TODO: verify media
