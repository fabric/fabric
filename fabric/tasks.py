import invoke

from .connection import Connection


class Task(invoke.Task):
    """
    Extends `invoke.tasks.Task` with knowledge of target hosts and similar.

    As `invoke.tasks.Task` relegates documentation responsibility to its `@task
    <invoke.tasks.task>` expression, so we relegate most details to our version
    of `@task <fabric.tasks.task>` - please see its docs for details.

    .. versionadded:: 2.1
    """

    def __init__(self, *args, **kwargs):
        # Pull out our own kwargs before hitting super, which will TypeError on
        # anything it doesn't know about.
        self.hosts = kwargs.pop("hosts", None)
        super().__init__(*args, **kwargs)


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

        These two value types *may* be mixed together in the same list, though
        we recommend that you keep things homogenous when possible, to avoid
        confusion when debugging.

        .. note::
            No automatic deduplication of values is performed; if you pass in
            multiple references to the same effective target host, the wrapped
            task will execute on that host multiple times (including making
            separate connections).

    .. versionadded:: 2.1
    """
    # Override klass to be our own Task, not Invoke's, unless somebody gave it
    # explicitly.
    kwargs.setdefault("klass", Task)
    return invoke.task(*args, **kwargs)


class ConnectionCall(invoke.Call):
    """
    Subclass of `invoke.tasks.Call` that generates `Connections <.Connection>`.
    """

    def __init__(self, *args, **kwargs):
        """
        Creates a new `.ConnectionCall`.

        Performs minor extensions to `~invoke.tasks.Call` -- see its docstring
        for most details. Only specific-to-subclass params are documented here.

        :param dict init_kwargs:
            Keyword arguments used to create a new `.Connection` when the
            wrapped task is executed. Default: ``None``.
        """
        init_kwargs = kwargs.pop("init_kwargs")  # , None)
        super().__init__(*args, **kwargs)
        self.init_kwargs = init_kwargs

    def clone_kwargs(self):
        # Extend superclass clone_kwargs to work in init_kwargs.
        # TODO: this pattern comes up a lot; is there a better way to handle it
        # without getting too crazy on the metaprogramming/over-engineering?
        # Maybe something attrs library can help with (re: declaring "These are
        # my bag-of-attributes attributes I want common stuff done to/with")
        kwargs = super().clone_kwargs()
        kwargs["init_kwargs"] = self.init_kwargs
        return kwargs

    def make_context(self, config):
        kwargs = self.init_kwargs
        # TODO: what about corner case of a decorator giving config in a hosts
        # kwarg member?! For now let's stomp on it, and then if somebody runs
        # into it, we can identify the use case & decide how best to deal.
        kwargs["config"] = config
        return Connection(**kwargs)

    def __repr__(self):
        ret = super().__repr__()
        if self.init_kwargs:
            ret = ret[:-1] + ", host='{}'>".format(self.init_kwargs["host"])
        return ret
