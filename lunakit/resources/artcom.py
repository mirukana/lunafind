# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

from typing import Any, Dict, List

import pendulum as pend

from .base import JsonResource

# pylint: disable=attribute-defined-outside-init


class Artcom(JsonResource):
    "Artist commentary."

    def __post_init__(self) -> None:
        super().__post_init__()
        self.has_artcom_tag = self.created_last_24h = None


    def get_if_post_has_resource(self) -> bool:
        check = ("commentary", "commentary_request")
        meta  = self.info["tag_string_meta"]
        # Make matching works if a tag is the first or last in the string
        # by putting things between spaces.
        self.has_artcom_tag = any(f" {tag} " in f" {meta} " for tag in check)

        # Posts made in last 24h may have not been auto-tagged yet.
        self.created_last_24h = (
            pend.parse(self.info["created_at"]) >= pend.yesterday()
        )

        if self.has_artcom_tag:
            return True

        if self.created_last_24h:
            return "Maybe"

        return False


    def get_data(self) -> List[Dict[str, Any]]:
        return self.client.artcom(self.post_id)
