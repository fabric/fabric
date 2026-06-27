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

    def __str__(self):
        # Without this, str(e) returns "" because args is empty — tracebacks become useless.
        failed = self.result.failed
        lines = ["{} hosts failed:".format(len(failed))]
        for cxn, exc in failed.items():
            lines.append("  {}: {!r}".format(cxn, exc))
        return "\n".join(lines)


class InvalidV1Env(Exception):
    """
    Raised when attempting to import a Fabric 1 ``env`` which is missing data.
    """

    pass
