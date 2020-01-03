from contextlib import contextmanager
import os
import re
import sys

from invoke.vendor.lexicon import Lexicon
from pytest_relaxed import trap

from fabric.main import make_program


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
        program = make_program()
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


def faux_v1_env():
    # Close enough to v1 _AttributeDict...
    # Contains a copy of enough of v1's defaults to prevent us having to do a
    # lot of extra .get()s...meh
    return Lexicon(
        always_use_pty=True,
        forward_agent=False,
        gateway=None,
        host_string="localghost",
        key_filename=None,
        no_agent=False,
        password=None,
        port=22,
        ssh_config_path=None,
        # Used in a handful of sanity tests, so it gets a 'real' value. eh.
        sudo_password="nope",
        sudo_prompt=None,
        timeout=None,
        use_ssh_config=False,
        user="localuser",
        warn_only=False,
    )
