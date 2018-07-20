"""Functions to work with files."""

import hashlib
import logging as log
import os

import simplejson


def _must_exist(path, must_exist, msg=None, force=False):
    if not must_exist and os.path.exists(path) and not force:
        log.warning(f"File '{path}' already exists, will not overwrite.")
        return False

    if must_exist and not os.path.exists(path) and not force:
        log.error(f"File '{path}' does not exist.")
        return False

    if msg:
        log.info(msg)
    return True


def write(content, path, mode="w", msg=None, chunk=False, overwrite=False):
    if not _must_exist(path, False, msg, overwrite):
        return False

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, mode) as output:
        if not chunk:
            output.write(content)
            return True

        for chunk_data in content:
            output.write(chunk_data)
    return True


def load_file(path, mode="r", msg=None, chunk_size=8 * 1024 ** 2):  # 8M
    if not _must_exist(path, True, msg):
        return False

    with open(path, mode) as input_:
        while True:
            data = input_.read(chunk_size)
            if not data:
                break
            yield data


def load_json(path, msg=None):
    if not _must_exist(path, True, msg):
        return False

    with open(path, "r") as json_file:
        return simplejson.load(json_file)


def get_file_md5(path, msg=None, chunk_size=8 * 1024 ** 2):  # 8M
    if not _must_exist(path, True, msg):
        return False

    hash_md5 = hashlib.md5()

    with open(path, "rb") as file_:
        while True:
            data = file_.read(chunk_size)
            if not data:
                break
            hash_md5.update(data)

    return hash_md5.hexdigest()
