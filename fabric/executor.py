from invoke import Call, Context, Executor, Task
from invoke.util import debug

from . import Connection
from .exceptions import NothingToDo


# TODO: come up w/ a better name heh
class FabExecutor(Executor):
    def expand_calls(self, calls, config):
        # Generate new call list with per-host variants & Connections inserted
        ret = []
        # TODO: mesh well with Invoke list-type args helper (inv #132)
        hosts = self.core[0].args.hosts.value
        hosts = hosts.split(',') if hosts else []
        for call in calls:
            # TODO: roles, other non-runtime host parameterizations, etc
            for host in hosts:
                # TODO: handle pre/post, which we are currently ignoring,
                # because it's poorly defined right now: does each
                # parameterized per-host task run its own pre/posts, or do they
                # run before/after the 'set' of per-host tasks? and etc
                ret.append(self.parameterize(call, host))
            # Deal with lack of hosts arg (acts same as `inv` in that case)
            if not hosts:
                call.context = Context(config=config)
                ret.append(call)
        # Add remainder as anonymous task
        if self.core.remainder:
            # TODO: this will need to change once there are more options for
            # setting host lists besides "-H or 100% within-task"
            if not hosts:
                raise NothingToDo("Was told to run a command, but not given any hosts to run it on!") # noqa
            def anonymous(c):
                c.run(self.core.remainder)
            anon = Call(Task(body=anonymous))
            # TODO: see above TODOs about non-parameterized setups, roles etc
            # TODO: will likely need to refactor that logic some more so it can
            # be used both there and here.
            for host in hosts:
                ret.append(self.parameterize(anon, host, config, True))
        return ret

    def parameterize(self, call, host, config, remainder=False):
        """
        Parameterize a Call with a given host.

        Involves cloning the call in question & updating its config w/ host.
        """
        debug("Parameterizing {0!r} for host {1!r}".format(call, host))
        clone = call.clone()
        # Generate a new config so they aren't shared
        config = self.config_for(clone, config, anonymous=remainder)
        # Make a new connection from the current host & config, set as context
        clone.context = Connection(host=host, config=config)
        return clone

    def dedupe(self, tasks):
        # Don't perform deduping, we will often have "duplicate" tasks w/
        # distinct host values/etc.
        # TODO: might want some deduplication later on though - falls under
        # "how to mesh parameterization with pre/post/etc deduping".
        return tasks
