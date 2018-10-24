# Copyright 2018 miruka
# This file is part of kana2, licensed under LGPLv3.

import threading

# Set the maximum number of total requests/threads that can be running at once.
# When doing Album.write(), a .write() thread will launch for every Post,
# and every Post will launch a .write() thread for every resource, etc.
MAX_PARALLEL_REQUESTS_SEMAPHORE = threading.BoundedSemaphore(8)

# pylint: disable=wrong-import-position
from .__about__ import __doc__
from .post import Post
from .stream import Stream
from .album import Album
