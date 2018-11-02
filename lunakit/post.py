# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

from typing import List, Optional, Union

from .attridict import AttrIndexedDict
from .clients import base, net
from .resources import Info, Resource


class Post(AttrIndexedDict, attr="title", map_partials=("update", "write")):
    "Collection of resources belonging to a specific post."

    def __init__(self,
                 id_or_url: Union[int, str]          = None,
                 prefer:    base.Client              = None,
                 resources: Optional[List[Resource]] = None) -> None:
        super().__init__()
        resources = list(resources) if resources else []

        client = prefer or net.DEFAULT


        if id_or_url:
            if str(id_or_url).startswith("http"):
                client = net.client_from_url(id_or_url)
                info   = next(client.info_url(id_or_url))
            else:
                info = client.info_id(id_or_url)

            passed_res = [type(r) for r in resources]

            for res in Resource.subclasses:
                if res not in passed_res:
                    resources.append(res(info, client))


        passed_info = [r for r in resources if isinstance(r, Info)]

        if not passed_info:
            raise TypeError("Info object required to initialize Post.")
        elif len(passed_info) > 1:
            raise TypeError("Too many Info object passed to Post, max is 1.")

        self.put(*resources)


    @property
    def id(self) -> int:
        return self["info"]["id"]

    @property
    def title(self) -> str:
        return self["info"]["title"]


    def __repr__(self) -> str:
        return f"%s(id={self.id}, title='{self.title}', has: %s)" % (
            type(self).__name__,
            ", ".join((k for k, r in self.data.items() if r.detected_resource))
        )
