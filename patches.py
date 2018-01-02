import cursor
import os
import sys
import ctypes
from pybooru.api_danbooru import DanbooruApi_Mixin


def cursor_hide():
    """
    Hide the terminal's cursor.
    Print the escape sequence on stderr instead of stdout to avoid leaks.
    """
    if os.name == 'nt':
        ci = cursor._CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == 'posix':
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def cursor_show():
    """
    Show the terminal's cursor.
    Print the escape sequence on stderr instead of stdout to avoid leaks.
    """

    if os.name == 'nt':
        ci = cursor._CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == 'posix':
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


cursor.hide = cursor_hide
cursor.show = cursor_show


def count_posts(self, tags):
    """
    Return the total number of posts on the booru, or the number for a
    specific tag search if a tags parameter is passed.
    Missing function added pybooru's Danbooru API.
    """
    return self._get("counts/posts.json", {"tags": tags})


DanbooruApi_Mixin.count_posts = count_posts
