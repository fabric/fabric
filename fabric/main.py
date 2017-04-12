"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

from invoke import Argument, Collection, Program
from invoke import __version__ as invoke
from paramiko import __version__ as paramiko

from . import __version__ as fabric
from . import Config
from .executor import FabExecutor
from .loader import FabfileLoader


class Fab(Program):
    def print_version(self):
        super(Fab, self).print_version()
        print("Paramiko {0}".format(paramiko))
        print("Invoke {0}".format(invoke))

    def core_args(self):
        core_args = super(Fab, self).core_args()
        my_args = [
            Argument(
                names=('F', 'ssh-config'),
                help="Path to runtime SSH config file.",
            ),
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

    def config_kwargs(self):
        # Obtain core config kwargs - eg hide, warn, etc
        kwargs = super(Fab, self).config_kwargs()
        # Add our own custom Config kwargs
        kwargs.update(dict(
            runtime_ssh_path=self.args['ssh-config'].value,
        ))
        return kwargs


program = Fab(
    name="Fabric",
    version=fabric,
    loader_class=FabfileLoader,
    executor_class=FabExecutor,
    config_class=Config,
)
