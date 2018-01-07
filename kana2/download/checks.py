import os
import shutil
import logging
import requests

from . import tools
from .. import utils

from . import site


def has_vital_keys(postDict, action, keys=["id"]):
    id_str = ""
    if "id" in postDict:
        id_str = " %s" % postDict["id"]

    for key in keys:
        if key not in postDict:
            logging.error("Unable to %s for post%s, missing %s" %
                          (action, id_str, key))
            if "id" in postDict:
                move_failed_dl(postDict["id"],
                               tools.get_file_to_dl_ext(postDict),
                               "missing-" + key)
            return False


def verify_dl(postID, mediaExt, method):
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
