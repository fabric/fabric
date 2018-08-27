try:
    from invoke.vendor.six.moves.queue import Queue
except ImportError:
    from six.moves.queue import Queue

from invoke.util import ExceptionHandlingThread

from .connection import Connection
from .exceptions import GroupException


class Group(list):
    """
    A collection of `.Connection` objects whose API operates on its contents.

    .. warning::
        **This is a partially abstract class**; you need to use one of its
        concrete subclasses (such as `.SerialGroup` or `.ThreadingGroup`) or
        you'll get ``NotImplementedError`` on most of the methods.

    Most methods in this class mirror those of `.Connection`, taking the same
    arguments; however their return values and exception-raising behavior
    differs:

    - Return values are dict-like objects (`.GroupResult`) mapping
      `.Connection` objects to the return value for the respective connections:
      `.Group.run` returns a map of `.Connection` to `.runners.Result`,
      `.Group.get` returns a map of `.Connection` to `.transfer.Result`, etc.
    - If any connections encountered exceptions, a `.GroupException` is raised,
      which is a thin wrapper around what would otherwise have been the
      `.GroupResult` returned; within that wrapped `.GroupResult`, the
      excepting connections map to the exception that was raised, in place of a
      ``Result`` (as no ``Result`` was obtained.) Any non-excepting connections
      will have a ``Result`` value, as normal.

    For example, when no exceptions occur, a session might look like this::

        >>> group = SerialGroup('host1', 'host2')
        >>> group.run("this is fine")
        {
            <Connection host='host1'>: <Result cmd='this is fine' exited=0>,
            <Connection host='host2'>: <Result cmd='this is fine' exited=0>,
        }

    With exceptions (anywhere from 1 to "all of them"), it looks like so; note
    the different exception classes, e.g. `~invoke.exceptions.UnexpectedExit`
    for a completed session whose command exited poorly, versus
    `socket.gaierror` for a host that had DNS problems::

        >>> group = SerialGroup('host1', 'host2', 'notahost')
        >>> group.run("will it blend?")
        {
            <Connection host='host1'>: <Result cmd='will it blend?' exited=0>,
            <Connection host='host2'>: <UnexpectedExit: cmd='...' exited=1>,
            <Connection host='notahost'>: gaierror(...),
        }

    As with `.Connection`, `.Group` objects may be used as context managers,
    which will automatically `.close` the object on block exit.

    .. versionadded:: 2.0
    .. versionchanged:: 2.4
        Added context manager behavior.
    """

    def __init__(self, *hosts, **kwargs):
        """
        Create a group of connections from one or more shorthand host strings.

        See `.Connection` for details on the format of these strings - they
        will be used as the first positional argument of `.Connection`
        constructors.

        Any keyword arguments given will be forwarded directly to those
        `.Connection` constructors as well. For example, to get a serially
        executing group object that connects to ``admin@host1``,
        ``admin@host2`` and ``admin@host3``, and forwards your SSH agent too::

            group = SerialGroup(
                "host1", "host2", "host3", user="admin", forward_agent=True,
            )

        .. versionchanged:: 2.3
            Added ``**kwargs`` (was previously only ``*hosts``).
        """
        # TODO: #563, #388 (could be here or higher up in Program area)
        self.extend([Connection(host, **kwargs) for host in hosts])

    @classmethod
    def from_connections(cls, connections):
        """
        Alternate constructor accepting `.Connection` objects.

        .. versionadded:: 2.0
        """
        # TODO: *args here too; or maybe just fold into __init__ and type
        # check?
        group = cls()
        group.extend(connections)
        return group

    def run(self, *args, **kwargs):
        """
        Executes `.Connection.run` on all member `Connections <.Connection>`.

        :returns: a `.GroupResult`.

        .. versionadded:: 2.0
        """
        # TODO: probably best to suck it up & match actual run() sig?
        # TODO: how to change method of execution across contents? subclass,
        # kwargs, additional methods, inject an executor? Doing subclass for
        # now, but not 100% sure it's the best route.
        # TODO: also need way to deal with duplicate connections (see THOUGHTS)
        # TODO: and errors - probably FailureSet? How to handle other,
        # regular, non Failure, exceptions though? Still need an aggregate
        # exception type either way, whether it is FailureSet or what...
        # TODO: OTOH, users may well want to be able to operate on the hosts
        # that did not fail (esp if failure % is low) so we really _do_ want
        # something like a result object mixing success and failure, or maybe a
        # golang style two-tuple of successes and failures?
        # TODO: or keep going w/ a "return or except", but the object is
        # largely similar (if not identical) in both situations, with the
        # exception just being the signal that Shit Broke?
        raise NotImplementedError

    # TODO: how to handle sudo? Probably just an inner worker method that takes
    # the method name to actually call (run, sudo, etc)?

    # TODO: this all needs to mesh well with similar strategies applied to
    # entire tasks - so that may still end up factored out into Executors or
    # something lower level than both those and these?

    # TODO: local? Invoke wants ability to do that on its own though, which
    # would be distinct from Group. (May want to switch Group to use that,
    # though, whatever it ends up being?)

    def get(self, *args, **kwargs):
        """
        Executes `.Connection.get` on all member `Connections <.Connection>`.

        :returns: a `.GroupResult`.

        .. versionadded:: 2.0
        """
        # TODO: probably best to suck it up & match actual get() sig?
        # TODO: actually implement on subclasses
        raise NotImplementedError

    def close(self):
        """
        Executes `.Connection.close` on all member `Connections <.Connection>`.

        .. versionadded:: 2.4
        """
        for cxn in self:
            cxn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class SerialGroup(Group):
    """
    Subclass of `.Group` which executes in simple, serial fashion.

    .. versionadded:: 2.0
    """

    def run(self, *args, **kwargs):
        results = GroupResult()
        excepted = False
        for cxn in self:
            try:
                results[cxn] = cxn.run(*args, **kwargs)
            except Exception as e:
                results[cxn] = e
                excepted = True
        if excepted:
            raise GroupException(results)
        return results


def thread_worker(cxn, queue, args, kwargs):
    result = cxn.run(*args, **kwargs)
    # TODO: namedtuple or attrs object?
    queue.put((cxn, result))


class ThreadingGroup(Group):
    """
    Subclass of `.Group` which uses threading to execute concurrently.

    .. versionadded:: 2.0
    """

    def run(self, *args, **kwargs):
        results = GroupResult()
        queue = Queue()
        threads = []
        for cxn in self:
            my_kwargs = dict(cxn=cxn, queue=queue, args=args, kwargs=kwargs)
            thread = ExceptionHandlingThread(
                target=thread_worker, kwargs=my_kwargs
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            # TODO: configurable join timeout
            # TODO: (in sudo's version) configurability around interactive
            # prompting resulting in an exception instead, as in v1
            thread.join()
        # Get non-exception results from queue
        while not queue.empty():
            # TODO: io-sleep? shouldn't matter if all threads are now joined
            cxn, result = queue.get(block=False)
            # TODO: outstanding musings about how exactly aggregate results
            # ought to ideally operate...heterogenous obj like this, multiple
            # objs, ??
            results[cxn] = result
        # Get exceptions from the threads themselves.
        # TODO: in a non-thread setup, this would differ, e.g.:
        # - a queue if using multiprocessing
        # - some other state-passing mechanism if using e.g. coroutines
        # - ???
        excepted = False
        for thread in threads:
            wrapper = thread.exception()
            if wrapper is not None:
                # Outer kwargs is Thread instantiation kwargs, inner is kwargs
                # passed to thread target/body.
                cxn = wrapper.kwargs["kwargs"]["cxn"]
                results[cxn] = wrapper.value
                excepted = True
        if excepted:
            raise GroupException(results)
        return results


class GroupResult(dict):
    """
    Collection of results and/or exceptions arising from `.Group` methods.

    Acts like a dict, but adds a couple convenience methods, to wit:

    - Keys are the individual `.Connection` objects from within the `.Group`.
    - Values are either return values / results from the called method (e.g.
      `.runners.Result` objects), *or* an exception object, if one prevented
      the method from returning.
    - Subclasses `dict`, so has all dict methods.
    - Has `.succeeded` and `.failed` attributes containing sub-dicts limited to
      just those key/value pairs that succeeded or encountered exceptions,
      respectively.

      - Of note, these attributes allow high level logic, e.g. ``if
        mygroup.run('command').failed`` and so forth.

    .. versionadded:: 2.0
    """

    def __init__(self, *args, **kwargs):
        super(dict, self).__init__(*args, **kwargs)
        self._successes = {}
        self._failures = {}

    def _bifurcate(self):
        # Short-circuit to avoid reprocessing every access.
        if self._successes or self._failures:
            return
        # TODO: if we ever expect .succeeded/.failed to be useful before a
        # GroupResult is fully initialized, this needs to become smarter.
        for key, value in self.items():
            if isinstance(value, BaseException):
                self._failures[key] = value
            else:
                self._successes[key] = value

    @property
    def succeeded(self):
        """
        A sub-dict containing only successful results.

        .. versionadded:: 2.0
        """
        self._bifurcate()
        return self._successes

    @property
    def failed(self):
        """
        A sub-dict containing only failed results.

        .. versionadded:: 2.0
        """
        self._bifurcate()
        return self._failures
