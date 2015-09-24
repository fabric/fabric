"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from mock import patch, ANY
from spec import Spec, assert_contains, eq_
from invoke.util import cd
from invoke import Context

from fabric.main import Fab, program as fab_program

from _util import expect, mock_remote


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

    @patch('fabric.main.Connection', spec=Context)
    def executes_remainder_as_anonymous_task(self, Connection):
        fab_program.run("fab -H myhost,otherhost -- lol a command", exit=False)
        # Did we connect to the hosts?
        eq_(Connection.call_args_list[0][1]['host'], 'myhost')
        eq_(Connection.call_args_list[1][1]['host'], 'otherhost')
        # Did we execute the command on both? (given same mock, just means
        # "did it run twice". Meh.)
        eq_(Connection.return_value.run.call_args_list[0][0][0], "lol a command")
        eq_(Connection.return_value.run.call_args_list[1][0][0], "lol a command")
