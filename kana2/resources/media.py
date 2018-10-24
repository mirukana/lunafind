# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

from typing import Generator

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
        response = self.client.http("get", self.info["dl_url"], stream=True)

        if not response:
            return None

        return response.iter_content(self.chunk_size)


    @property
    def msg_writing(self) -> str:
        return f"Downloading {self.title} for post {self.post_id}..."


    @property
    def msg_no_data_found(self) -> str:
        return f"No {self.title} found for post {self.post_id}."
