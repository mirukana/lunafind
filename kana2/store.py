"""Store class"""

import logging as log

from . import Post, utils
from .client import DEFAULT as CLIENT_DEFAULT


class Store(dict):
    def __init__(self, *values, store_dict=None, client=CLIENT_DEFAULT):
        self._client = client

        if store_dict:
            # Make a Store from the Store __dict__ received.
            super().__init__(store_dict)  # dict(store_dict)
            return

        posts_found = 0
        for value in values:
            # The value is a Post object:
            if isinstance(value, Post):
                self[value.id] = value
                posts_found   += 1
                log.info(f"Added post {value.id}, total: {posts_found}.")
                utils.blank_line()
                continue

            # Else, the value is a query to call _client.info_auto() on:
            query_found = 0
            for post in self._client.info_auto(value):
                query_found     += 1
                self[post["id"]] = Post(info=post, _blank_line=False)
            posts_found += query_found

            if query_found > 0:
                log.info(f"Found {query_found} posts from query '{value}', "
                         f"total: {posts_found}.")

            utils.blank_line()  # After each set_paths() → get_extra() calls

        if posts_found > 1:
            log.info(f"Found {posts_found} total posts.")
            utils.blank_line()

    # Store operations:

    def __add__(self, to_add):  # + operator
        store = to_add if isinstance(to_add, Store) else Store(to_add)
        new   = self.copy()
        new.update(store)
        return new

    def __iadd__(self, to_add):  # += operator
        self = self + to_add
        return self

    def merge(self, *to_merge):
        for value in to_merge:
            store = value if isinstance(value, Store) else Store(value)
            self.update(store)
        return self

    # Store items removals:

    def __sub__(self, to_sub):  # -
        store = to_sub if isinstance(to_sub, Store) else Store(to_sub)
        new   = self.copy()
        for key in store:
            new.pop(key, None)
        return new

    def __isub__(self, to_sub):  # -=
        self = self - to_sub
        return self

    def subtract(self, *to_sub):
        for value in to_sub:
            store = value if isinstance(value, Store) else Store(value)
            for key in store:
                self.pop(key, None)
        return self

    # Adding single Post objects:

    def __setitem__(self, key, new_post):  # Store[new] = val
        new_post = new_post if isinstance(new_post, Post) else Post(new_post)
        self.update({key: new_post})

    def setdefault(self, key, default_post=None):
        if not default_post:
            return self.get(key)

        if key not in self.keys():
            self[key] = Post(default_post)

        return self[key]

    # Display:

    def __repr__(self):
        return "Store(%r)" % {k: p for k, p in self.items()}

    def __str__(self):
        return str({k: p for k, p in self.items()})

    # Comparisons:

    def __eq__(self, other_store):
        if len(self.keys()) != len(other_store.keys()):
            return False

        for key, post in self.items():
            if post != other_store.get(key):
                return False

        return True

    # Others:

    def copy(self):
        """Override dict.copy() to return a Store()."""
        return Store(store_dict={k: p for k, p in self.items()})

    def map(self, method, *args, **kwargs):
        in_store = len(self.keys())

        for i, post in enumerate(self.values()):
            log.info(f"Applying {method}() on post {i + 1}/{in_store}: "
                     f"{post.id}")
            getattr(post, method)(*args, **kwargs)
        return self


def _set_post_map_functions():
    def new(target_post_function):
        def template(self, *args, **kwargs):
            return self.map(target_post_function, *args, **kwargs)
        return template

    functions = (
        "get_all", "get_extra", "get_media", "get_artcom", "get_notes",
        "set_paths", "write", "verify_media"
    )

    for function in functions:
        setattr(Store, function, new(function))


Store.__copy__ = Store.copy
_set_post_map_functions()
