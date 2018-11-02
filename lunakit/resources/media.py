# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

from typing import Generator

from .. import utils
from .base import Resource


class Media(Resource):
    "Post image or webm."

    def __post_init__(self) -> None:
        super().__post_init__()

        self.binary = True

        if not self.info["is_broken"]:
            self.ext = self.info["dl_ext"]


    def get_if_post_has_resource(self) -> bool:
        return False if self.info["is_broken"] else True


    def get_data(self) -> Generator[bytes, None, None]:
        return self.client.media(self.info)


    def write(self, overwrite: bool = False, warn: bool = True):
        if self.info["is_broken"]:
            return None

        return super().write(overwrite, warn)


    @property
    def msg_writing(self) -> str:
        return f"Downloading {self.ext} of %s for post {self.post_id}" % (
            utils.bytes2human(self.info["dl_size"])
            if "dl_size" in self.info else "unknown size"
        )


    @property
    def msg_no_data_found(self) -> str:
        return f"No {self.title} found for post {self.post_id}."
