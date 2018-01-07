import json
import logging
import multiprocessing
import time
import requests
import pybooru.resources as booruRes

from . import checks
from . import tools
from .. import utils

from . import processes_nbr
from . import site


def posts(postList):
    print("Downloading %d posts, about %s%s\n" %
          (len(postList),
           utils.bytes2human(tools.dl_size(postList)),
           next((" max" for p in postList if p["file_ext"] == "zip"), "")))

    pool = multiprocessing.Pool(processes_nbr)
    pool.map(post, postList)


def post(postDict):
    media(postDict)
    infos(postDict)


def infos(postDict, addDlTime=True, indent=4):
    utils.make_dirs("infos")

    if checks.has_vital_keys(postDict, "write JSON") is False:
        return False

    if addDlTime:
        # Example date: 2016-11-24T02:30-04:00
        t = time.strftime("%FT%T%z")
        postDict["download_time"] = t[:22] + ":" + t[-2:]

    with open("infos/%d.json" % postDict["id"], "w") as jsonFile:
        json.dump(postDict, jsonFile, indent=indent, ensure_ascii=False)


def media(postDict, chunkSize=16 * 1024 ** 2):
    utils.make_dirs("media")

    check_keys = ["id", "file_url", "large_file_url", "md5"]
    if checks.has_vital_keys(postDict, "download media", check_keys) is False:
        return False

    postID = postDict["id"]
    mediaURL = site + postDict["file_url"]
    verify_integrity_method = "md5", postDict["md5"]

    # If the post is an ugoira, get the associated video instead of the zip.
    if postDict["file_ext"] == "zip":
        mediaURL = site + postDict["large_file_url"]
        verify_integrity_method = "filesize", postDict["large_file_url"]

    mediaExt = tools.get_file_to_dl_ext(postDict)

    logging.info("Downloading media for post %d" % postID)

    req = requests.get(mediaURL, stream=True, timeout=60)
    if req.status_code not in range(200, 204 + 1):
        logging.error("Failed media download for post %d: %s" %
                      (postID, booruRes.HTTP_STATUS_CODE[req.status_code][0]))
        checks.move_failed_dl(postID, mediaExt, "error-%s" % req.status_code)
        return False

    with open("media/%s.%s" % (postID, mediaExt), "wb") as mediaFile:
        for chunk in req.iter_content(chunkSize):
            if chunk:
                mediaFile.write(chunk)

    checks.verify_dl(postID, mediaExt, verify_integrity_method)
