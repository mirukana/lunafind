# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

"Functions to work with files."

import os
from types import GeneratorType

import simplejson
from atomicfile import AtomicFile
from zenlog import log


def write(content, path, binary=False, overwrite=False):
    if os.path.exists(path) and not overwrite:
        log.warn("File %r already exists, will not overwrite.", path)
        return False

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with AtomicFile(path, "wb" if binary else "w") as out_file:
        if isinstance(content, GeneratorType):
            for chunk in content:
                out_file.write(chunk)
        else:
            out_file.write(content)

    return True


def load_file(path, mode="r", json=False):
    if not os.path.exists(path):
        log.error("File %r does not exist.", path)
        return None

    with open(path, mode) as in_file:
        return simplejson.load(in_file) if json else in_file.read()
