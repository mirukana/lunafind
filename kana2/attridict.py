# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import abc
import collections
import copy
from typing import Tuple

from zenlog import log


class AttrIndexedDict(collections.UserDict, abc.ABC):
    "Dictionary where items are indexed by a specific attribute they possess."

    def __init_subclass__(cls, attr: str, sugar_map: Tuple[str], **kwargs
                         ) -> None:
        super().__init_subclass__(**kwargs)
        cls.attr = attr

        for method in sugar_map:
            func = lambda self, m=method, *a, **kw: cls.map(self, m, *a, **kw)
            setattr(cls, method, func)


    def __setitem__(self, key, value) -> None:
        raise RuntimeError("Use %s.put() to add items." % type(self).__name__)


    def __getattr__(self, name: str):
        "Allow accessing dict items with a dot like attributes."
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError(f"No attribute or dict key named {name!r}.")


    def map(self, method: str, *args, _quiet: bool = True, **kwargs
           ) -> "AttrIndexedDict":
        "Run a method of all stored items with optional args and kwargs."
        num   = 1
        total = len(self.data)

        for k, item in self.data.items():
            if not _quiet:
                log.info("Running %s() on %r (%d/%d)", method, k, num, total)

            getattr(item, method)(*args, **kwargs)
            num += 1

        return self


    def copy(self) -> "AttrIndexedDict":
        return copy.copy(self)


    def put(self, *items) -> "AttrIndexedDict":
        "Add items to the dict that will be indexed by self.attr."
        for item in items:
            self.data[getattr(item, self.attr)] = item
        return self

    # album << item, item >> album
    __lshift__ = __rrshift__ = lambda self, item: self.put(item)


    def merge(self, *others: "AttrIndexedDict") -> "AttrIndexedDict":
        for other in others:
            self.data.update(other)
        return self

    def __add__(self, other: "AttrIndexedDict") -> "AttrIndexedDict":
        return self.copy().merge(other)


    def difference(self, *others: "AttrIndexedDict") -> "AttrIndexedDict":
        new = self.copy()
        for other in others:
            for key in other:
                try:
                    del new[key]
                except KeyError:
                    pass
        return new

    def __sub__(self, other: "AttrIndexedDict") -> "AttrIndexedDict":
        return self.copy().difference(other)
