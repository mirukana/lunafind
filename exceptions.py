class QueryBooruError(Exception):
    def __init__(self, http_code, url):
        self._msg = "Unable to complete request, error %s from '%s'." % \
                (http_code, url)

    def __str__(self):
        return self._msg
