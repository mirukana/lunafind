"""Functions to work with files."""

import hashlib
import json
import logging as log
import os

from . import config


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


def load_file(path, mode="r", msg=None, chunk_size=config.CHUNK_SIZE):
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
        return json.load(json_file)


def get_file_md5(path, msg=None, chunk_size=config.CHUNK_SIZE):
    """Calculate a file's MD5 hash.

    Args:
        file_path (str): Path of the file to calculate hash.
        chunk_size (int, optional): Maximum size of a chunk to be loaded in
            RAM. Defaults to `16 * 1024 ** 2` (16 MB).

    Returns:
        (str): The MD5 hash of the given file.

    Examples:
        >>> utils.get_file_md5("/dev/null")
        'd41d8cd98f00b204e9800998ecf8427e'
    """
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
