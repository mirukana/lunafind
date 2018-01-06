#!/usr/bin/env python3
import utils
import sys
import os
import shutil
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


def getDlFileExt(postDict):
    # TODO: Config option to download normal zip instead.
    try:
        if postDict["file_url"].endswith(".zip"):
            return postDict["large_file_url"].split(".")[-1]
        return postDict["file_ext"]
    except KeyError:
        return "UNKNOWN"


def has_vital_keys(postDict, action, keys=["id"]):
    id_str = ""
    if "id" in postDict:
        id_str = " %s" % postDict["id"]

    for key in keys:
        if key not in postDict:
            logging.error("Unable to %s for post%s, missing %s" %
                          (action, id_str, key))
            if "id" in postDict:
                move_failed_dl(postDict["id"], getDlFileExt(postDict),
                               "missing-" + key)
            return False


def approx_dl_size(postList):
    return sum(post["file_size"] for post in postList)


def download_list(postList):
    print("Downloading %d posts for a maximum of about %s\n" %
          (len(postList), utils.bytes2human(approx_dl_size(postList))))

    pool = multiprocessing.Pool(processes)
    pool.map(download, postList)


def download(postDict):
    if save_infos(postDict) or download_media(postDict) is False:
        return False


def save_infos(postDict, indent=4):
    utils.make_dirs("infos")

    if has_vital_keys(postDict, "write JSON") is False:
        return False

    with open("infos/%d.json" % postDict["id"], "w") as jsonFile:
        json.dump(postDict, jsonFile, indent=indent, ensure_ascii=False)


def download_media(postDict, chunkSize=16 * 1024 ** 2):
    utils.make_dirs("media")

    check_keys = ["id", "file_url", "large_file_url", "md5"]
    if has_vital_keys(postDict, "download media", check_keys) is False:
        return False

    postID = postDict["id"]
    mediaURL = site + postDict["file_url"]
    verify_integrity_method = "md5", postDict["md5"]

    # If the post is an ugoira, get the associated video instead of the zip.
    if postDict["file_ext"] == "zip":
        mediaURL = site + postDict["large_file_url"]
        verify_integrity_method = "filesize", postDict["large_file_url"]

    mediaExt = getDlFileExt(postDict)

    logging.info("Downloading media for post %d" % postID)

    req = requests.get(mediaURL, stream=True, timeout=60)
    if req.status_code not in range(200, 204 + 1):
        logging.error("Failed media download for post %d: %s" %
                      (postID, booruRes.HTTP_STATUS_CODE[req.status_code][0]))
        move_failed_dl(postID, mediaExt, "error-%s" % req.status_code)
        return False

    with open("media/%s.%s" % (postID, mediaExt), "wb") as mediaFile:
        for chunk in req.iter_content(chunkSize):
            if chunk:
                mediaFile.write(chunk)

    verify_dl_integrity(postID, mediaExt, verify_integrity_method)


def verify_dl_integrity(postID, mediaExt, method):
    media = "media/%s.%s" % (postID, mediaExt)

    if not (method[0] == "md5" and utils.get_file_md5(media) == method[1] or

            method[0] == "filesize" and method[1] == os.path.getsize(media) or

            method[0] == "filesize" and
            requests.head(site + method[1]).headers["content-length"] !=
            os.path.getsize(media)):
        logging.error("Corrupted download, %s check failed." % method[0])
        move_failed_dl(postID, mediaExt, method[0] + "-mismatch")


def move_failed_dl(postID, mediaExt, errorDir):
    media = "media/", "%s.%s" % (postID, mediaExt)
    infos = "infos/", "%s.json" % postID

    for path in media, infos:
        utils.make_dirs("%s/%s" % (path[0], errorDir))
        try:
            dirFile = "".join(path)
            shutil.move(dirFile, dirFile.replace("/", "/%s/" % errorDir, 1))
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
