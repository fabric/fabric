"""
Custom Fabric exception classes.

Most are simply distinct Exception subclasses for purposes of message-passing (though typically still in actual error situations.)
"""

class NetworkError(Exception):
    def __init__(self, message, wrapped):
        self.message = message
        self.wrapped = wrapped

class FabfileError(IOError):
    """Raised when a fabric file is not found"""
