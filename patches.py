from pybooru.api_danbooru import DanbooruApi_Mixin


def count_posts(self, tags):
    """
    Return the total number of posts on the booru, or the number for a
    specific tag search if a tags parameter is passed.
    Missing function added pybooru's Danbooru API.
    """
    return self._get("counts/posts.json", {"tags": tags})


DanbooruApi_Mixin.count_posts = count_posts
