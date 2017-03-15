from invoke.vendor.six.moves.queue import Queue

from invoke.util import ExceptionHandlingThread

from fabric import Connection


class Group(list):
    """
    A collection of `.Connection` objects whose API operates on its contents.

    This is a partially abstract class; see its subclasses for details on how
    they are implemented..

    Most methods in this class mirror those of `.Connection`, taking the same
    arguments; however their return values and exception-raising behavior
    differs:

    - Return values are dicts mapping `.Connection` objects to the return
      value for the respective connections, so e.g. `.Group.run` returns a map
      of `.Connection` to `.Result`.
    - If any connections encountered exceptions, a `.GroupException` is raised,
      which is a thin wrapper around what would otherwise have been the dict
      returned; within that dict, the excepting connections map to the
      exception that was raised, in place of a `.Result` (as no `.Result` was
      obtained.) Any non-excepting connections will have a `.Result` value, as
      normal.

    For example, when no exceptions occur, a session might look like this::

        >>> group = Group('host1', 'host2')
        >>> group.run("this is fine")
        {
            <Connection host='host1'>: <Result cmd='this is fine' exited=0>,
            <Connection host='host2'>: <Result cmd='this is fine' exited=0>,
        }

    With exceptions (anywhere from 1 to "all of them"), it looks like so; note
    the different exception classes, e.g. `.UnexpectedExit` for a completed
    session whose command exited poorly, versus `socket.gaierror` for a host
    that had DNS problems::

        >>> group = Group('host1', 'host2', 'notahost')
        >>> group.run("will it blend?")
        {
            <Connection host='host1'>: <Result cmd='will it blend?' exited=0>,
            <Connection host='host2'>: <UnexpectedExit: cmd='...' exited=1>,
            <Connection host='notahost'>: gaierror(...),
        }

    """
    def __init__(self, *hosts):
        """
        Create a group of connections from one or more shorthand strings.

        See `.Connection` for details on the format of these strings - they
        will be used as the first positional argument of `.Connection`
        constructors.
        """
        # TODO: #563, #388 (could be here or higher up in Program area)
        self.extend(map(Connection, hosts))

    @classmethod
    def from_connections(cls, connections):
        """
        Alternate constructor accepting `.Connection` objects.
        """
        # TODO: *args here too; or maybe just fold into __init__ and type
        # check?
        group = cls()
        group.extend(connections)
        return group

    def run(self, *args, **kwargs):
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

    # TODO: mirror Connection's close()?

    # TODO: execute() as mentioned in tutorial


class SerialGroup(Group):
    """
    Subclass of `.Group` which executes in simple, serial fashion.
    """
    def run(self, *args, **kwargs):
        results = GroupResult()
        for cxn in self:
            try:
                results[cxn] = cxn.run(*args, **kwargs)
            except Exception as e:
                results[cxn] = e
        return results


def thread_worker(cxn, queue, args, kwargs):
    result = cxn.run(*args, **kwargs)
    # TODO: namedtuple or attrs object?
    queue.put((cxn, result))

class ThreadingGroup(Group):
    """
    Subclass of `.Group` which uses threading to execute concurrently.
    """
    def run(self, *args, **kwargs):
        results = GroupResult()
        queue = Queue()
        threads = []
        for cxn in self:
            my_kwargs = dict(
                cxn=cxn,
                queue=queue,
                args=args,
                kwargs=kwargs,
            )
            thread = ExceptionHandlingThread(
                target=thread_worker,
                kwargs=my_kwargs,
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
        for thread in threads:
            wrapper = thread.exception()
            if wrapper is not None:
                # Outer kwargs is Thread instantiation kwargs, inner is kwargs
                # passed to thread target/body.
                cxn = wrapper.kwargs['kwargs']['cxn']
                results[cxn] = wrapper.value
        return results


class GroupResult(dict):
    """
    Collection of results and/or exceptions arising from `.Group` methods.

    Acts like a dict, but adds a couple convenience methods, to wit:

    - Keys are the individual `.Connection` objects from within the `.Group`.
    - Values are either return values / results from the called method (e.g.
      `.Result` objects), *or* an exception object, if one prevented the method
      from returning.
    - Subclasses `dict`, so has all dict methods.
    - Has `.succeeded` and `.failed` attributes containing sub-dicts limited to
      just those key/value pairs that succeeded or encountered exceptions,
      respectively.

      - Of note, these attributes allow high level logic, e.g. ``if
        mygroup.run('command').failed`` and so forth.
    """
    pass
