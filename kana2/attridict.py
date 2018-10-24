# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import abc
import collections
import copy
import functools
from multiprocessing.pool import ThreadPool
from typing import Tuple

from . import MAX_TOTAL_THREADS_SEMAPHORE


class AttrIndexedDict(collections.UserDict, abc.ABC):
    "Dictionary where items are indexed by a specific attribute they possess."

    def __init_subclass__(cls,
                          attr:         str,
                          map_partials: Tuple[str] = (),
                          **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.attr = attr

        for method in map_partials:
            setattr(cls, method, functools.partialmethod(cls.map, method))


    def __setitem__(self, key, value) -> None:
        raise RuntimeError("Use %s.put() to add items." % type(self).__name__)


    def __getattr__(self, name: str):
        "Allow accessing dict items with a dot like attributes."
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError(f"No attribute or dict key named {name!r}.")


    def map(self, method: str, *args, _threaded: bool = True, **kwargs
           ) -> "AttrIndexedDict":
        "For all stored items, run a method they possess."

        def work(item) -> None:
            getattr(item, method)(*args, **kwargs)

        if _threaded:
            pool = ThreadPool(processes=8)
            pool.map(work, self.data.values())
            return self

        for item in self.data.values():
            with MAX_TOTAL_THREADS_SEMAPHORE:
                work(item)
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
