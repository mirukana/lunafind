# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import abc
import os
import pprint
import textwrap
from typing import Any, Dict, Optional, Union

from dataclasses import dataclass, field
from zenlog import log

from .. import clients, io, utils


@dataclass(repr=False)
class Resource(abc.ABC):
    """Represent a Post's resource, such as its info, content, or other extras.

    Class attributes:
        title:      Resource name.
        ext:        Extension for the file to be written.
        binary:     Whether 'wb' or 'w' mode will be used to write the file.
        chunk_size: Size of chunks for HTTP transfers.

    Attributes:
        info:   Info resource object corresponding to the post.
        client: Booru client, object from kana2.clients.
    """

    subclasses = []

    info:   Union["Info", Dict[str, Any]] = field(default_factory=dict)
    client: clients.Client                = field(default=None)

    _data: Any = field(init=False, default=None)


    def __repr__(self) -> str:
        data  = pprint.pformat(self.data, width=80 - 4)
        lines = len(data.splitlines())

        return "%s(client.name=%r, post_id=%r, data=%s)" % (
            type(self).__name__,
            self.client.name,
            self.post_id,
            "\\\n%s\n" % textwrap.indent(data, "   ") if lines > 1 else data
        )


    def __init_subclass__(cls,
                          ext:    Optional[str] = None,
                          binary: bool          = False,
                          **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        cls.subclasses.append(cls)

        cls.title:      str           = cls.__name__.lower()
        cls.ext:        Optional[str] = ext or getattr(cls, "ext", None)
        cls.binary:     bool          = binary
        cls.chunk_size: int           = 8 * 10124 ** 2


    def __post_init__(self) -> None:
        assert self.info
        self.info = self.info or {}  # for pylint - Info *are* subscriptable

        if not self.client:
            self.client = getattr(self.info, "client", "") or clients.DEFAULT


    @property
    def post_id(self) -> int:
        return self.info["id"]


    @property
    def detected_resource(self) -> Union[bool, str]:
        """If post should have the wanted resource. True, False or 'Maybe'.
        Determined from info and used to avoid useless net requests.
        """
        detected = self.get_if_post_has_resource()

        if not detected and self.msg_no_data_found:
            log.warn(self.msg_no_data_found)

        return detected


    @property
    def data(self) -> Any:
        "Actual resource data, lazy-fetched when this property is accessed."
        if self._data:
            return self._data

        if not self.detected_resource:
            return None

        if self.msg_fetching:
            log.info(self.msg_fetching)

        # pylint: disable=assignment-from-none
        self._data = self.get_data()

        if self._data in (None, [], (), {}, ""):  # False or 0 are ok
            if self.msg_no_data_found:
                log.info(self.msg_no_data_found)
            return None

        return self._data

    def update(self, accept_gone: bool = False) -> "Resource":
        """Forget already fetched data and re-fetch, except if
        accept_gone is False and nothing is found (e.g. post deleted)."""
        old_data   = self._data
        # pylint: disable=assignment-from-none
        self._data = self.get_data()

        if self._data in (None, [], (), {}, ""):
            if self.msg_update_fail:
                log.warn(self.msg_update_fail)

            if not accept_gone:
                self._data = old_data

        return self


    @property
    def path(self) -> str:
        "Path where to save serialized file to."
        return self.get_path()


    def write(self, overwrite=False) -> "Resource":
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


    def get_data(self) -> Any:
        "Retrieve and return data from network."
        return None


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


class JsonResource(Resource, binary=False, ext="json"):
    def get_serialized(self) -> str:
        "Return JSONified data to be written to disk."
        if not self.data:
            return None

        return utils.jsonify(self.data)


    def __getattr__(self, name: str):
        """Allow accessing resource data dict with a dot like attributes.
        Warning: dict items can't be set/edited/deleted when accessed like so.
        """
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError(f"No attribute or dict key named {name!r}.")
