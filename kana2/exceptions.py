"""Exceptions specific to kana2."""

class QueryBooruError(Exception):
    """Giving up after receiving too many errors from the booru.

    Args:
        http_code (int): HTTP Error code from the booru.
        url (str): Booru API request URL that failed.

    Attributes:
        msg (str): String to be printed when the error is raised.
    """

    def __init__(self, http_code, url):
        self._msg = "Unable to complete request, error %s from '%s'." % \
                (http_code, url)

    def __str__(self):
        return self._msg
