"""kana2 global variables"""

from . import net

CLIENT     = net.get_booru_client("safebooru")
CHUNK_SIZE = 8 * 1024 ** 2  # 8 MiB
