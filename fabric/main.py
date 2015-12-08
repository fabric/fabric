"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

from invoke import (
    Program, FilesystemLoader, Argument, Task, Executor, Collection, Call,
)
from invoke import __version__ as invoke
from invoke.util import debug
from paramiko import __version__ as paramiko

from . import __version__ as fabric
from . import Config, Connection


class Fab(Program):
    def print_version(self):
        super(Fab, self).print_version()
        print("Paramiko {0}".format(paramiko))
        print("Invoke {0}".format(invoke))

    def core_args(self):
        core_args = super(Fab, self).core_args()
        my_args = [
            Argument(
                names=('H', 'hosts'),
                help="Comma-separated host name(s) to execute tasks against.",
            ),
        ]
        return core_args + my_args

    @property
    def _remainder_only(self):
        return not self.core.unparsed and self.core.remainder

    def load_collection(self):
        # Stick in a dummy Collection if it looks like we were invoked w/o any
        # tasks, and with a remainder.
        # This isn't super ideal, but Invoke proper has no obvious "just run my
        # remainder" use case, so having it be capable of running w/o any task
        # module, makes no sense. But we want that capability for testing &
        # things like 'fab -H x,y,z -- mycommand'.
        if self._remainder_only:
            self.collection = Collection()
        else:
            super(Fab, self).load_collection()

    def no_tasks_given(self):
        # As above, neuter the usual "hey you didn't give me any tasks, let me
        # print help for you" behavior, if necessary.
        if not self._remainder_only:
            super(Fab, self).no_tasks_given()


# TODO: come up w/ a better name heh
class FabExecutor(Executor):
    def expand_tasks(self, tasks, config):
        # Generate new call list with per-host variants & Connections inserted
        ret = []
        hosts = self.core[0].args.hosts.value.split(',')
        for task in tasks:
            for host in hosts:
                # TODO: handle pre/post, which we are currently ignoring
                #   (see parent class' implementation)
                ret.append(self.parameterize(task, host, config))
        # Add remainder as anonymous task
        if self.core.remainder:
            def anonymous(c):
                c.run(self.core.remainder)
            anon = Call(Task(body=anonymous, contextualized=True))
            for host in hosts:
                ret.append(self.parameterize(anon, host, config, True))
        return ret

    def parameterize(self, task, host, config, remainder=False):
        # Give it a Connection as its Context (and see Connection's own
        # TODO note regarding merging it & Context itself)
        # TODO: clone task before mutating
        debug("Parameterizing {0!r} for host {1!r}".format(task, host))
        config = self.config_for(task, config, anonymous=remainder)
        task.context = Connection(host=host, config=config)
        return task

    def dedupe(self, tasks):
        # Don't perform deduping, we will often have "duplicate" tasks w/
        # distinct host values/etc.
        # TODO: might want some deduplication later on though - falls under
        # "how to mesh parameterization with pre/post/etc deduping".
        return tasks


class FabfileLoader(FilesystemLoader):
    # TODO: we may run into issues re: swapping loader "strategies" (eg
    # FilesystemLoader vs...something else eventually) versus this sort of
    # "just tweaking DEFAULT_COLLECTION_NAME" setting. Maybe just make the
    # default collection name itself a runtime option?
    DEFAULT_COLLECTION_NAME = 'fabfile'


program = Fab(
    name="Fabric",
    version=fabric,
    loader_class=FabfileLoader,
    executor_class=FabExecutor,
    config_class=Config,
)
