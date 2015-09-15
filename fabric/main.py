"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

from invoke import Program, __version__ as invoke
from paramiko import __version__  as paramiko

from . import __version__ as fabric


program = Program(
    name="Fabric",
    version=fabric,
    #subversions=???
)
