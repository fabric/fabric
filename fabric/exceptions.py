# TODO: this may want to move to Invoke if we can find a use for it there too?
# Or make it _more_ narrowly focused and stay here?
class NothingToDo(Exception):
    pass


class GroupException(Exception):
    """
    Lightweight exception wrapper for `.GroupResult` when one contains errors.

    .. versionadded:: 2.0
    """

    def __init__(self, result):
        #: The `.GroupResult` object which would have been returned, had there
        #: been no errors. See its docstring (and that of `.Group`) for
        #: details.
        self.result = result


class InvalidV1Env(Exception):
    """
    Raised when attempting to import a Fabric 1 ``env`` which is missing data.
    """

    pass
