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
        self.result = result
