"""Functions to work with files."""

import hashlib
import json
import logging as log
import os

from . import config


def write(content, to_path, mode="w", msg=None, chunk=False, overwrite=False):
    os.makedirs(os.path.dirname(to_path), exist_ok=True)

    if os.path.exists(to_path) and not overwrite:
        log.warning(f"File '{to_path}' already exists, will not overwrite.")
        return False

    if msg:
        log.info(msg)

    with open(to_path, mode) as output:
        if not chunk:
            output.write(content)
            return True

        for chunk_data in content:
            output.write(chunk_data)
    return True


def load_file(in_path, mode="r", chunk_size=config.CHUNK_SIZE):
    with open(in_path, mode) as input_:
        while True:
            data = input_.read(chunk_size)
            if not data:
                break
            yield data


def load_json(in_path):
    with open(in_path, "r") as json_file:
        return json.load(json_file)


def get_file_md5(file_path, chunk_size=config.CHUNK_SIZE):
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
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as file_:
        while True:
            data = file_.read(chunk_size)
            if not data:
                break
            hash_md5.update(data)

    return hash_md5.hexdigest()
