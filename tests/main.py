"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import re
import sys

from spec import Spec, trap, assert_contains

from fabric.main import program


class Fab_(Spec):
    @trap
    def version_output_contains_our_name_plus_deps(self):
        program.run("fab --version", exit=False)
        expected = r"""
Fabric .+
Paramiko .+
Invoke .+
""".strip()
        assert_contains(sys.stdout.getvalue(), expected)

    @trap
    def help_output_says_fab(self):
        program.run("fab --help", exit=False)
        assert "Usage: fab " in sys.stdout.getvalue()
