import invoke
from invoke import Call, Task
from invoke.util import debug

from . import Connection
from .exceptions import NothingToDo


class Executor(invoke.Executor):
    """
    `~invoke.executor.Executor` subclass which understands Fabric concepts.

    Designed to work in tandem with Fabric's `@task
    <fabric.tasks.task>`/`~fabric.tasks.Task`, and is capable of acting on
    information stored on the resulting objects -- such as default host lists.

    This class is written to be backwards compatible with vanilla Invoke-level
    tasks, which it simply delegates to its superclass.

    Please see the parent class' `documentation <invoke.executor.Executor>` for
    details on most public API members and object lifecycle.
    """

    def expand_calls(self, calls, apply_hosts=True):
        # Generate new call list with per-host variants & Connections inserted
        ret = []
        hosts = []
        host_str = self.core[0].args.hosts.value
        if apply_hosts and host_str:
            hosts = host_str.split(",")
        for call in calls:
            if isinstance(call, Task):
                call = Call(task=call)
            # TODO: expand this to allow multiple types of execution plans,
            # pending outcome of invoke#461 (which, if flexible enough to
            # handle intersect of dependencies+parameterization, just becomes
            # 'honor that new feature of Invoke')
            # TODO: roles, other non-runtime host parameterizations, etc
            # Pre-tasks get added only once, not once per host.
            ret.extend(self.expand_calls(call.pre, apply_hosts=False))
            # Main task, per host
            for host in hosts:
                ret.append(self.parameterize(call, host))
            # Deal with lack of hosts arg (acts same as `inv` in that case)
            # TODO: no tests for this branch?
            if not hosts:
                ret.append(call)
            # Post-tasks added once, not once per host.
            ret.extend(self.expand_calls(call.post, apply_hosts=False))
        # Add remainder as anonymous task
        if self.core.remainder:
            # TODO: this will need to change once there are more options for
            # setting host lists besides "-H or 100% within-task"
            if not hosts:
                raise NothingToDo(
                    "Was told to run a command, but not given any hosts to run it on!"  # noqa
                )

            def anonymous(c):
                # TODO: how to make all our tests configure in_stream=False?
                c.run(self.core.remainder, in_stream=False)

            anon = Call(Task(body=anonymous))
            # TODO: see above TODOs about non-parameterized setups, roles etc
            # TODO: will likely need to refactor that logic some more so it can
            # be used both there and here.
            for host in hosts:
                ret.append(self.parameterize(anon, host))
        return ret

    def parameterize(self, call, host):
        """
        Parameterize a Call with its Context set to a per-host Config.
        """
        debug("Parameterizing {!r} for host {!r}".format(call, host))
        # Generate a custom ConnectionCall that knows how to yield a Connection
        # in its make_context(), specifically one to the host requested here.
        clone = call.clone(into=ConnectionCall)
        # TODO: using bag-of-attrs is mildly gross but whatever, I'll take it.
        clone.host = host
        return clone

    def dedupe(self, tasks):
        # Don't perform deduping, we will often have "duplicate" tasks w/
        # distinct host values/etc.
        # TODO: might want some deduplication later on though - falls under
        # "how to mesh parameterization with pre/post/etc deduping".
        return tasks


class ConnectionCall(Call):
    """
    Subclass of `invoke.tasks.Call` that generates `Connections <.Connection>`.
    """

    def make_context(self, config):
        return Connection(host=self.host, config=config)
