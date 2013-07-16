"""
Custom Fabric exception classes.

Most are simply distinct Exception subclasses for purposes of message-passing
(though typically still in actual error situations.)
"""


class NetworkError(Exception):
    # Must allow for calling with zero args/kwargs, since pickle is apparently
    # stupid with exceptions and tries to call it as such when passed around in
    # a multiprocessing.Queue.
    def __init__(self, message=None, wrapped=None):
        self.message = message
        self.wrapped = wrapped

    def __str__(self):
        return self.message

    def __repr__(self):
        return "%s(%s) => %r" % (
            self.__class__.__name__, self.message, self.wrapped
        )


class CommandTimeout(Exception):
    pass
