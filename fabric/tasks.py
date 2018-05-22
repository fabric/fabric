import invoke


class Task(invoke.Task):
    """
    Extends `invoke.tasks.Task` with knowledge of target hosts and similar.

    As `invoke.tasks.Task` relegates documentation responsibility to its `@task
    <invoke.tasks.task>` expression, so we relegate most of our useful docs to
    our own `@task <fabric.tasks.task>` - please see its docs for details.

    .. versionadded:: 2.1
    """


def task(*args, **kwargs):
    """
    Wraps/extends Invoke's `@task <invoke.tasks.task>` with extra kwargs.

    See `the Invoke-level API docs <invoke.tasks.task>` for most details; this
    Fabric-specific implementation adds the following additional keyword
    arguments:

    :param hosts:
        An iterable of host-connection specifiers appropriate for eventually
        instantiating a `.Connection`. The existence of this argument will
        trigger automatic parameterization of the task when invoked from the
        CLI, similar to the behavior of :option:`--hosts`.

        .. note::
            This parameterization is "lower-level" than that driven by
            :option:`--hosts`: if a task decorated with this parameter is
            executed in a session where :option:`--hosts` was given, the
            CLI-driven value will win out.
        
        List members may be one of:

        - A string appropriate for being the first positional argument to
          `.Connection` - see its docs for details, but these are typically
          shorthand-only convenience strings like ``hostname.example.com`` or
          ``user@host:port``.
        - A dictionary appropriate for use as keyword arguments when
          instantiating a `.Connection`. Useful for values that don't mesh well
          with simple strings (e.g. statically defined IPv6 addresses) or to
          bake in more complex info (eg ``connect_timeout``, ``connect_kwargs``
          params like auth info, etc).

    .. versionadded:: 2.1
    """
    pass
