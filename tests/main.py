"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from mock import patch
from spec import Spec, assert_contains
from invoke.util import cd

from fabric.main import Fab

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

    @mock_remote()
    def executes_remainder_as_anonymous_task(self, chan):
        # Because threading arbitrary mocks into @mock_remote is kinda hard
        with patch('fabric.connection.Connection') as Connection:
            Fab().run("fab -H myhost,otherhost -- lol a command", exit=False)
            # Did we connect to the hosts?
            Connection.assert_called_with("myhost")
            Connection.assert_called_with("otherhost")
            # Did we execute the command on both?
            # TODO: how to tell these apart exactly ,do we need to update
            # mock_remote? =/
            chan.exec_command.assert_called_with("lol a command")
            chan.exec_command.assert_called_with("lol a command")
