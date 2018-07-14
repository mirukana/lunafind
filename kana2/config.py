"""kana2 global variables"""

import pybooru

CLIENT     = pybooru.Danbooru("safebooru")
CHUNK_SIZE = 8 * 1024 ** 2  # 8 MiB
