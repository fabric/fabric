from contextlib import contextmanager
import os
import re
import sys

from pytest_relaxed import trap

from fabric import Connection as Connection_, Config as Config_
from fabric.main import program as fab_program
from paramiko import SSHConfig


support = os.path.join(os.path.abspath(os.path.dirname(__file__)), "_support")
config_file = os.path.abspath(os.path.join(support, "config.yml"))

# TODO: move invoke's support_path + load + etc somewhere importable? or into
# pytest-relaxed, despite it not being strictly related to that feature set?
# ugh
@contextmanager
def support_path():
    sys.path.insert(0, support)
    try:
        yield
    finally:
        sys.path.pop(0)


def load(name):
    with support_path():
        imported = __import__(name)
        return imported


# TODO: this could become a fixture in conftest.py, presumably, and just yield
# stdout, allowing the tests themselves to assert more naturally
@trap
def expect(invocation, out, program=None, test="equals"):
    if program is None:
        program = fab_program
    program.run("fab {}".format(invocation), exit=False)
    output = sys.stdout.getvalue()
    if test == "equals":
        assert output == out
    elif test == "contains":
        assert out in output
    elif test == "regex":
        assert re.match(out, output)
    else:
        err = "Don't know how to expect that <stdout> {} <expected>!"
        assert False, err.format(test)


# Locally override Connection, Config with versions that supply a dummy
# SSHConfig and thus don't load any test-running user's own ssh_config files.
# TODO: find a cleaner way to do this, though I don't really see any that isn't
# adding a ton of fixtures everywhere (and thus, opening up to forgetting it
# for new tests...)
class Config(Config_):
    def __init__(self, *args, **kwargs):
        wat = "You're giving ssh_config explicitly, please use Config_!"
        assert "ssh_config" not in kwargs, wat
        # Give ssh_config explicitly -> shorter way of turning off loading
        kwargs["ssh_config"] = SSHConfig()
        super(Config, self).__init__(*args, **kwargs)


class Connection(Connection_):
    def __init__(self, *args, **kwargs):
        # Make sure we're using our tweaked Config if none was given.
        kwargs.setdefault("config", Config())
        super(Connection, self).__init__(*args, **kwargs)
