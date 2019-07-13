import invoke
from invoke import Call, Task

from .tasks import ConnectionCall
from .exceptions import NothingToDo
from .util import debug


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

    def normalize_hosts(self, hosts):
        """
        Normalize mixed host-strings-or-kwarg-dicts into kwarg dicts only.

        In other words, transforms data taken from the CLI (--hosts, always
        strings) or decorator arguments (may be strings or kwarg dicts) into
        kwargs suitable for creating Connection instances.

        Subclasses may wish to override or extend this to perform, for example,
        database or custom config file lookups (vs this default behavior, which
        is to simply assume that strings are 'host' kwargs).

        :param hosts:
            Potentially heterogenous list of host connection values, as per the
            ``hosts`` param to `.task`.

        :returns: Homogenous list of Connection init kwarg dicts.
        """
        dicts = []
        for value in hosts or []:
            # Assume first posarg to Connection() if not already a dict.
            if not isinstance(value, dict):
                value = dict(host=value)
            dicts.append(value)
        return dicts

    def expand_calls(self, calls, apply_hosts=True):
        # Generate new call list with per-host variants & Connections inserted
        ret = []
        cli_hosts = []
        host_str = self.core[0].args.hosts.value
        if apply_hosts and host_str:
            cli_hosts = host_str.split(",")
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
            # Determine final desired host list based on CLI and task values
            # (with CLI, being closer to runtime, winning) and normalize to
            # Connection-init kwargs.
            call_hosts = getattr(call, "hosts", None)
            cxn_params = self.normalize_hosts(cli_hosts or call_hosts)
            # Main task, per host/connection
            for init_kwargs in cxn_params:
                ret.append(self.parameterize(call, init_kwargs))
            # Deal with lack of hosts list (acts same as `inv` in that case)
            # TODO: no tests for this branch?
            if not cxn_params:
                ret.append(call)
            # Post-tasks added once, not once per host.
            ret.extend(self.expand_calls(call.post, apply_hosts=False))
        # Add remainder as anonymous task
        if self.core.remainder:
            # TODO: this will need to change once there are more options for
            # setting host lists besides "-H or 100% within-task"
            if not cli_hosts:
                raise NothingToDo(
                    "Was told to run a command, but not given any hosts to run it on!"  # noqa
                )

            def anonymous(c):
                c.run(self.core.remainder)

            anon = Call(Task(body=anonymous))
            # TODO: see above TODOs about non-parameterized setups, roles etc
            # TODO: will likely need to refactor that logic some more so it can
            # be used both there and here.
            for init_kwargs in self.normalize_hosts(cli_hosts):
                ret.append(self.parameterize(anon, init_kwargs))
        return ret

    def parameterize(self, call, connection_init_kwargs):
        """
        Parameterize a Call with its Context set to a per-host Connection.

        :param call:
            The generic `.Call` being parameterized.
        :param connection_init_kwargs:
            The dict of `.Connection` init params/kwargs to attach to the
            resulting `.ConnectionCall`.

        :returns:
            `.ConnectionCall`.
        """
        msg = "Parameterizing {!r} with Connection kwargs {!r}"
        debug(msg.format(call, connection_init_kwargs))
        # Generate a custom ConnectionCall that has init_kwargs (used for
        # creating the Connection at runtime) set to the requested params.
        new_call_kwargs = dict(init_kwargs=connection_init_kwargs)
        clone = call.clone(into=ConnectionCall, with_=new_call_kwargs)
        return clone

    def dedupe(self, tasks):
        # Don't perform deduping, we will often have "duplicate" tasks w/
        # distinct host values/etc.
        # TODO: might want some deduplication later on though - falls under
        # "how to mesh parameterization with pre/post/etc deduping".
        return tasks
