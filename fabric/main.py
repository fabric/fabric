"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

from invoke import Program, __version__ as invoke
from paramiko import __version__ as paramiko

from . import __version__ as fabric


class Fab(Program):
    def print_version(self):
        super(Fab, self).print_version()
        print("Paramiko {0}".format(paramiko))
        print("Invoke {0}".format(invoke))

program = Fab(
    name="Fabric",
    version=fabric,
)
