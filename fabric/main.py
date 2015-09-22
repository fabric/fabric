"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

from invoke import Program, FilesystemLoader, Argument, Task, Executor
from invoke import __version__ as invoke
from paramiko import __version__ as paramiko

from . import __version__ as fabric


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
                help="Host name(s) to execute tasks against.",
            ),
        ]
        return core_args + my_args


# TODO: come up w/ a better name heh
class FabExecutor(Executor):
    def expand_tasks(self, tasks):
        # We still want pre/post tasks expanded, so run our parent
        tasks = super(FabExecutor, self).expand_tasks(tasks)
        # Then tack on remainder to the end, if necessary
        if self.core.remainder:
            def anonymous(c):
                c.run(self.core.remainder)
            tasks.append(Task(body=anonymous, contextualized=True))
        return tasks

# TODO: would be nice to run w/o a fabfile present if we give a remainder
# TODO: this also means running w/o any tasks, so tweaking core program loop
# TODO: the above is present in Fab 1 and isn't SUPER required (it does nothing
# you can't do w/ vanilla ssh client) but nice-to-have for backwards compat /
# testing / etc.


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
)
