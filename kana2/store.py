"""Store class"""

import logging as log

from . import Post, info, utils

POST_USABLE_FUNCTIONS = [
    "get_all", "get_extra", "get_media", "get_artcom", "get_notes",
    "set_paths", "write", "verify_media"
]


class Store(dict):
    def __init__(self, *values, store_dict=None):
        if store_dict:
            super().__init__(store_dict)
            return

        posts_found = 0
        for value in values:
            if isinstance(value, Post):
                self[value.id] = value
                posts_found   += 1
                log.info(f"Added post {value.id}, total: {posts_found}.")
                utils.blank_line()
                continue

            query_found = 0
            for post in info.from_auto(value):
                query_found     += 1
                self[post["id"]] = Post(info=post, _blank_line=False)

            posts_found += query_found
            if query_found > 0:
                log.info(f"Found {query_found} posts, total: {posts_found}.")

            utils.blank_line()  # After each set_paths() → get_extra() calls

        log.info(f"Found {posts_found} total posts.")
        utils.blank_line()

    # Store merges:

    def __add__(self, to_add):  # +
        store = to_add if isinstance(to_add, Store) else Store(to_add)
        new   = self.copy()
        new.update(store)
        return new

    def __iadd__(self, to_add):  # +=
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
        """Override dict append to return a Store()."""
        return Store(store_dict={k: p for k, p in self.items()})

    def map(self, method, *args, **kwargs):
        for store_post in self.values():
            getattr(store_post, method)(*args, **kwargs)
        return self


Store.__copy__ = Store.copy

# Hack to make functions that operate on all posts,
# e.g. Store.get_all() calls Post.get_all on all Post objects.
for function in POST_USABLE_FUNCTIONS:
    # pylint: disable=w0122
    exec(f"def {function}(self, *args, **kwargs):\n"
         f"    return self.map('{function}', *args, **kwargs)\n"
         f"Store.{function} = {function}", globals())
