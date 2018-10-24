# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import abc
import inspect
import os
import pprint
import textwrap
from typing import Any, Dict, Optional, Union

from cached_property import cached_property
from dataclasses import dataclass, field
from zenlog import log

from .. import clients, io, utils


@dataclass(repr=False)
class Resource(abc.ABC):
    """Represent a Post's resource, such as its info, content, or other extras.

    Class attributes:
        title: Resource name in lowercase.

    Attributes:
        info:       Info resource object corresponding to the post.
        client:     Booru client, object from kana2.clients.
        ext:        Extension for the file to be written.
        binary:     Whether 'wb' or 'w' mode will be used to write the file.
        chunk_size: Size of chunks for HTTP transfers, default is 8 MiB.
    """

    subclasses = []

    info:   Union["Info", Dict[str, Any]] = field(default_factory=dict)
    client: clients.Client                = field(default=None)

    ext:        Optional[str] = field(default=None,          repr=False)
    binary:     bool          = field(default=False,         repr=False)
    chunk_size: int           = field(default=8 * 1024 ** 2, repr=False)


    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        if not inspect.isabstract(cls):
            cls.subclasses.append(cls)

        cls.title: str = cls.__name__.lower()


    def __post_init__(self) -> None:
        assert self.info, "Missing post informations to initialize resource."
        self.info = self.info or {}  # for pylint - Info *are* subscriptable

        if not self.client:
            self.client = getattr(self.info, "client", "") or clients.DEFAULT


    def __repr__(self) -> str:
        data  = pprint.pformat(self.data, width=80 - 4)
        lines = len(data.splitlines())

        return "%s(client.name=%r, post_id=%r, data=%s)" % (
            type(self).__name__,
            self.client.name,
            self.post_id,
            "\\\n%s\n" % textwrap.indent(data, "   ") if lines > 1 else data
        )


    @property
    def post_id(self) -> int:
        return self.info["id"]


    @cached_property
    def detected_resource(self) -> Union[bool, str]:
        """If post should have the wanted resource. True, False or 'Maybe'.
        Determined from info and used to avoid useless net requests.
        """
        detected = self.get_if_post_has_resource()

        if not detected and self.msg_no_data_found:
            log.warn(self.msg_no_data_found)

        return detected


    @cached_property
    def data(self) -> Any:
        "Actual resource data, lazy-fetched when this property is accessed."
        if not self.detected_resource:
            return None

        if self.msg_fetching:
            log.info(self.msg_fetching)

        # pylint: disable=assignment-from-none
        got = self.get_data()

        if not got and got not in (0, False):
            if self.msg_no_data_found:
                log.info(self.msg_no_data_found)
            return None

        return got


    def update(self, accept_gone: bool = False) -> "Resource":
        """Forget already fetched data and re-fetch, except if
        accept_gone is False and nothing is found (e.g. post deleted).
        """
        if "data" not in self.__dict__:
            # pylint: disable=pointless-statement
            self.data
            return self

        # pylint: disable=assignment-from-none
        new_data = self.get_data()

        if not new_data and new_data not in (0, False):
            if self.msg_update_fail:
                log.warn(self.msg_update_fail)

            if accept_gone:
                self.__dict__["data"] = new_data
        else:
            self.__dict__["data"] = new_data

        return self


    @property
    def path(self) -> str:
        "Path where to save serialized file to."
        return self.get_path()


    def write(self, overwrite: bool = False) -> "Resource":
        "Write serialized resource data to disk."
        if self.msg_writing:
            log.info(self.msg_writing)

        content = self.get_serialized()

        if content is not None:
            io.write(content, self.path, self.binary, overwrite)

        return self


    # Get functions, override in subclasses when necessary.
    # pylint: disable=no-self-use

    def get_if_post_has_resource(self) -> bool:
        "Test and return if post has the needed resource."
        return True


    @abc.abstractmethod
    def get_data(self) -> Any:
        "Retrieve and return data from network."
        pass


    def get_serialized(self) -> Any:
        "Return serialized data to be written to disk."
        return self.data


    def get_path(self) -> str:
        "Return path where to save serialized file to."
        name = self.client.name
        ext  = f".{self.ext}" if self.ext else ""
        return f"{name}-{self.post_id}{os.sep}{self.title}{ext}"


    # Messages, override in subclasses when neccessary.

    @property
    def msg_no_data_found(self) -> Optional[str]:
        return None


    @property
    def msg_update_fail(self) -> Optional[str]:
        return f"Updating {self.title} for post {self.post_id} returned " \
               f"nothing. Resource gone?"


    @property
    def msg_fetching(self) -> Optional[str]:
        return None


    @property
    def msg_writing(self) -> Optional[str]:
        return None


class JsonResource(Resource, abc.ABC):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.ext = "json"


    @abc.abstractmethod
    def get_data(self) -> Any:
        "Retrieve and return data from network."
        pass

    def get_serialized(self) -> str:
        "Return JSONified data to be written to disk."
        if not self.data:
            return None

        return utils.jsonify(self.data)


    def __getitem__(self, key):
        return self.data[key]


    def __setitem__(self, key, value) -> None:
        self.data[key] = value


    def __delitem__(self, key) -> None:
        del self.data[key]


    def __getattr__(self, name: str):
        """Allow accessing resource data dict with a dot like attributes.
        Warning: dict items can't be set/edited/deleted when accessed like so.
        """
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError(f"No attribute or dict key named {name!r}.")
