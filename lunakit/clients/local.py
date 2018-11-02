# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

from pathlib import Path
from typing import Any, Dict, List, Union

from dataclasses import dataclass

from . import base


@dataclass
class Local(base.Client):
    path: Union[Path, str] = Path(".")


    def __post_init__(self) -> None:
        self.path = Path(self.path)


    def info_search(self,
                    tags:   str                = "",
                    pages:  base.PageType      = 1,
                    limit:  base.Optional[int] = None,
                    random: bool               = False,
                    raw:    bool               = False) -> base.InfoGenType:

        all_posts = sorted(self.path.iterdir(),
                           key     = lambda p: int(p.name.split("-")[-1]),
                           reverse = True)

        # for post in all_posts:



    def artcom(self, post_id: int) -> List[Dict[str, Any]]:
        return []


    def notes(self, post_id: int) -> List[Dict[str, Any]]:
        return []


    def count_posts(self, tags: str = "") -> int:
        return 0
