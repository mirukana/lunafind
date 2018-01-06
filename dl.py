#!/usr/bin/env python3
import utils
import sys
import os
import json
import logging
import multiprocessing
import requests
import pybooru.resources as booruRes

# TODO: Move thoses to config
site = "https://safebooru.donmai.us"
processes = 16


def main():
    logging.basicConfig(level=logging.INFO)
    download_list(load_infos())


def load_infos():
    # TODO: accept python dict from ./query
    if not os.isatty(0):  # If something is piped
        return json.load(sys.stdin)

    if os.path.isfile(sys.argv[-1]):
        return json.load(open(sys.argv[-1]))

    # TODO: print help


def post_has_keys(postDict, action, keys=["id"]):
    id_str = ""
    if "id" in postDict:
        id_str = " " + str(postDict["id"])

    for key in keys:
        if key not in postDict:
            logging.error("Unable to %s for post%s, missing %s" %
                          (action, id_str, key))
            return False


def approx_dl_size(postList):
    return sum(post["file_size"] for post in postList)


def download_list(postList):
    print("Downloading %d posts for about %s\n" %
          (len(postList), utils.bytes2human(approx_dl_size(postList))))

    pool = multiprocessing.Pool(processes)
    pool.map(download, postList)


def download(postDict):
    if download_infos(postDict) is False:
        return False

    download_media(postDict)


def download_infos(postDict, indent=4):
    utils.make_dirs("infos")

    if post_has_keys(postDict, "write JSON") is False:
        return False

    with open("infos/%d.json" % postDict["id"], "w") as jsonFile:
        json.dump(postDict, jsonFile, indent=indent, ensure_ascii=False)


def download_media(postDict):
    utils.make_dirs("media")

    if post_has_keys(postDict, "download media", ["id", "file_url"]) is False:
        return False

    post_id = postDict["id"]
    media_url = site + postDict["file_url"]

    # If the post is an ugoira, try to get the associated video.
    if media_url.endswith(".zip"):
        media_url = site + postDict["large_file_url"]

    media_ext = media_url.split(".")[-1]

    logging.info("Downloading media for post %d" % post_id)

    req = requests.get(media_url, stream=True, timeout=60)
    if req.status_code not in range(200, 204 + 1):
        logging.error("Failed media download for post %d: %s" %
                      (post_id, booruRes.HTTPError[req.status_code][0]))

    with open("media/%s.%s" % (post_id, media_ext), "wb") as mediaFile:
        for chunk in req.iter_content(chunk_size=16 * 1024 ** 2):
            if chunk:
                mediaFile.write(chunk)

    # TODO: Check for corruption.


if __name__ == "__main__":
    main()
