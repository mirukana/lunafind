"""kana2 exceptions"""


def get_post_id(post):
    return str(post.get("id", "without ID"))


class Kana2Error(Exception):
    def __init__(self, message, post, print_err=True):
        self.post      = post
        self.print_err = print_err
        super().__init__(message)


class CriticalKeyError(Kana2Error):
    def __init__(self, post, missing_key, msg_end="skipping", print_err=True):
        self.missing_key = missing_key
        self.message     = "Post %s is missing critical %s key, %s" % \
                           (get_post_id(post), missing_key, msg_end)
        super().__init__(self.message, post, print_err)


class AddExtraKeyError(Kana2Error):
    def __init__(self, post, missing_key, cannot_add, print_err=True):
        self.missing_key = missing_key
        self.cannot_add  = cannot_add
        self.message     = "Post %s is missing %s key, cannot add %s" % \
                           (get_post_id(post), missing_key, cannot_add)
        super().__init__(self.message, post, print_err)


class VerifyError(Kana2Error):
    def __init__(self, check, post, file_path, expected, got, print_err=True):
        self.file_path = file_path
        self.expected  = expected
        self.got       = got
        self.message   = "%s check failed for post %s ('%s'): " \
                         "expected %s, got %s" % \
                         (check, get_post_id(post), file_path, expected, got)
        super().__init__(self.message, post, print_err)


class MD5VerifyError(VerifyError):
    def __init__(self, post, file_path, expected, got, print_err=True):
        super().__init__("MD5", post, file_path, expected, got, print_err)


class FilesizeVerifyError(VerifyError):
    def __init__(self, post, file_path, expected, got, print_err=True):
        expected = "%s bytes" % expected
        super().__init__("Filesize", post, file_path, expected, got, print_err)
