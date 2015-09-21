"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from spec import Spec, assert_contains
from invoke.util import cd

from _util import expect


class Fab_(Spec):
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

    def help_output_says_fab(self):
        expect("--help", "Usage: fab", test=assert_contains)

    def loads_fabfile_not_tasks(self):
        "Loads fabfile.py, not tasks.py"
        with cd(os.path.join(os.path.dirname(__file__), '_support')):
            expect(
                "--list",
                """
Available tasks:

  build
  deploy

""".lstrip()
            )

    def exposes_hosts_flag_in_help(self):
        expect("--help", "-H STRING, --hosts=STRING", test=assert_contains)
