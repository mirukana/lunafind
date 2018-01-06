from pybooru.api_danbooru import DanbooruApi_Mixin
import pybooru.resources


def count_posts(self, tags):
    """
    Return the total number of posts on the booru, or the number for a
    specific tag search if a tags parameter is passed.
    Missing function added pybooru's Danbooru API.
    """
    return self._get("counts/posts.json", {"tags": tags})


DanbooruApi_Mixin.count_posts = count_posts

# HTTPS for Danbooru and Konachan, add Safebooru
pybooru.resources.SITE_LIST["konachan"]["url"] = "https://konachan.com"
for booru in "danbooru", "safebooru":
    pybooru.resources.SITE_LIST[booru]["url"] = "https://%s.donmai.us" % booru
