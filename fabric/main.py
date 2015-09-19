"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

from invoke import Program, __version__ as invoke, FilesystemLoader, Argument
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
)
