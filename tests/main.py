"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import sys

from spec import Spec, trap, assert_contains, eq_
from invoke.util import cd

from fabric.main import program as fab_program


# TODO: figure out a non shite way to share Invoke's more beefy copy of same.
def expect(invocation, out, program=None, test=None):
    if program is None:
        program = fab_program
    program.run("fab {0}".format(invocation), exit=False)
    (test or eq_)(sys.stdout.getvalue(), out)


class Fab_(Spec):
    @trap
    def version_output_contains_our_name_plus_deps(self):
        expect(
            "--version",
            r"""
Fabric .+
Paramiko .+
Invoke .+
""".strip(),
            test=assert_contains
        )

    @trap
    def help_output_says_fab(self):
        expect("--help", "Usage: fab", test=assert_contains)

    @trap
    def loads_fabfile_not_tasks(self):
        "Loads fabfile.py, not tasks.py"
        with cd('tests/_support'):
            expect(
                "--list",
                """
Available tasks:

  build
  deploy

""".lstrip()
            )
