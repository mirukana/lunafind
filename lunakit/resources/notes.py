# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

from typing import Any, Dict, List

from .base import JsonResource


class Notes(JsonResource):
    "Bubbles over images (e.g. translations)."

    def get_if_post_has_resource(self) -> bool:
        return bool(self.info["last_noted_at"])


    def get_data(self) -> List[Dict[str, Any]]:
        return self.client.api("note_list", post_id=self.post_id)
