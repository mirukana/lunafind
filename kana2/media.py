"""Get media from booru posts"""

import logging
import os

from . import CLIENT, errors, extra, reqwrap, utils


def media(post, chunk_size=16 * 1024 ** 2, client=CLIENT):
    if not isinstance(post, dict):
        raise TypeError("Expected one query dictionary, got %s." % type(post))

    post = extra.add_keys_if_needed(post, client)

    try:
        url  = post["kana2_dl_url"]
        ext  = post["kana2_dl_ext"]
        size = post["kana2_dl_size"]
    except KeyError as err:
        raise errors.CriticalKeyError(post, err.args[0], "cannot fetch media")

    logging.info("Retrieving media (%s, %s) for post %s",
                 ext, utils.bytes2human(size), post.get("id", "without ID"))

    req = reqwrap.http("get", url, client.client, stream=True)
    yield from req.iter_content(chunk_size)


def verify(post, file_path, client=CLIENT):
    post = extra.add_keys_if_needed(post, client)

    try:
        if not post["kana2_is_ugoira"] and "md5" in post:
            verify_md5(post, file_path, post["md5"])
        else:
            verify_filesize(post, file_path, post["kana2_dl_size"])
    except KeyError as err:
        raise errors.CriticalKeyError(post, err.args[0], "cannot verify media")


def verify_md5(post, file_path, expected_md5):
    actual_md5 = utils.get_file_md5(file_path)

    if actual_md5 != expected_md5:
        raise errors.MD5VerifyError(post, file_path, expected_md5, actual_md5)


def verify_filesize(post, file_path, expected_bytesize):
    actual_size = os.path.getsize(file_path)

    if actual_size != int(expected_bytesize):
        raise errors.FilesizeVerifyError(post, file_path,
                                         expected_bytesize, actual_size)
