from pybooru.api_danbooru import DanbooruApi_Mixin


def count_posts(self, tags):
    return self._get("counts/posts.json", {"tags": tags})


DanbooruApi_Mixin.count_posts = count_posts
