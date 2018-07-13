"""kana2 exceptions"""

from pybooru.resources import HTTP_STATUS_CODE as HTTP_BOORU_CODES

from . import net


def get_post_id(post):
    return str(post.get("id", "without ID"))


class Kana2Error(Exception):
    def __init__(self, message, print_err=True):
        self.message   = message
        self.print_err = print_err
        super().__init__(self.message)

# Network errors

class RetryError(Kana2Error):
    def __init__(self, err_code, url, tried_times, max_tries, giving_up=False,
                 print_err=True):
        self.err_code    = err_code
        self.url         = url
        self.tried_times = tried_times
        self.max_tries   = max_tries
        self.print_err   = print_err
        self.giving_up   = giving_up

        wait         = "giving up" if giving_up else "retrying in %ss" % \
                            net.get_retrying_in_time(tried_times)
        short_msg    = HTTP_BOORU_CODES[err_code][0]
        details      = HTTP_BOORU_CODES[err_code][1]
        self.message = (f"Request failed, {wait} ({tried_times}/{max_tries}): "
                        f"{err_code} - {short_msg}, {details} - URL: {url}")
        super().__init__(self.message)

    def __reduce__(self):
        return RetryError, \
               (self.err_code, self.url, self.tried_times, self.max_tries,
                self.giving_up)

# Media verification errors

class VerifyError(Kana2Error):
    def __init__(self, check, post, file_path, expected, got, print_err=True):
        self.check     = check
        self.post      = post
        self.file_path = file_path
        self.expected  = expected
        self.got       = got
        self.message   = "%s check failed for post %s ('%s'): " \
                         "expected %s, got %s" % \
                         (check, get_post_id(post), file_path, expected, got)
        super().__init__(self.message, print_err)

    def __reduce__(self):
        return VerifyError, \
               (self.check, self.post, self.file_path, self.expected, self.got)


class MD5VerifyError(VerifyError):
    def __init__(self, post, file_path, expected, got, print_err=True):
        super().__init__("MD5", post, file_path, expected, got, print_err)

    def __reduce__(self):
        return MD5VerifyError, \
               (self.post, self.file_path, self.expected, self.got)


class FilesizeVerifyError(VerifyError):
    def __init__(self, post, file_path, expected, got, print_err=True):
        expected = "%s bytes" % expected
        super().__init__("Filesize", post, file_path, expected, got, print_err)

    def __reduce__(self):
        return FilesizeVerifyError, \
               (self.post, self.file_path, self.expected, self.got)