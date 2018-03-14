import json
import logging
import multiprocessing
import os

from . import PROCESSES, media, tools, utils


def posts(posts_):
    posts_ = list(posts_)

    logging.info("Downloading %d posts, estimated %s",
                 len(posts_),
                 utils.bytes2human(get_dl_size(posts_)))

    pool = multiprocessing.Pool(PROCESSES)
    pool.map(one_post, posts_)


def one_post(post,
             info_dest="info/{id}.json",
             media_dest="media/{id}.{file_ext}",
             notes_dest="notes/{id}.json",
             artcom_dest="artcom/{id}.json"):

    def write_content(content, dest, mode="w"):
        if dest:
            utils.make_dirs(os.path.split(dest)[0])
            utils.chunk_write(content, tools.replace_keys(post, dest), mode)

    write_content(json.dumps(post, ensure_ascii=False, sort_keys=True),
                  info_dest)
    write_content(media.media(post), media_dest, "wb")


def get_dl_size(post_list):
    return sum(post["file_size"] for post in post_list)
