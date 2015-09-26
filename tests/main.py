"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from mock import patch
from spec import Spec, assert_contains, eq_, skip
from invoke.util import cd

from fabric import Connection
from fabric.main import program as fab_program

from _util import expect, mock_remote


_support = os.path.join(os.path.dirname(__file__), '_support')


class Fab_(Spec):
    class core_program_behavior:
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

        def exposes_hosts_flag_in_help(self):
            expect("--help", "-H STRING, --hosts=STRING", test=assert_contains)

        @mock_remote()
        def executes_remainder_as_anonymous_task(self, chan):
            # contextmanager because hard to thread extra mocks into the
            # decorator
            mock = patch('fabric.main.Connection', wraps=Connection)
            with mock as MConnection:
                fab_program.run("fab -H myhost -- whoami", exit=False)
                # Did we connect to the host?
                # (not using assert_called_with because using mock.ANY causes
                # funky blowups when comparing with Config objects)
                eq_(MConnection.call_args[1]['host'], 'myhost')
                # Did we execute the command?
                chan.exec_command.assert_called_with('whoami')


    class fabfiles:
        def loads_fabfile_not_tasks(self):
            "Loads fabfile.py, not tasks.py"
            with cd(_support):
                expect(
                    "--list",
                    """
Available tasks:

  basic_run
  build
  deploy

""".lstrip()
                )


    class hosts_flag_parameterizes_tasks:
        @mock_remote()
        def single_string_is_single_host_and_single_exec(self, chan):
            # In addition to just testing a base case, this checks for a really
            # dumb bug where one appends to, instead of replacing, the task
            # list during parameterization/expansion XD
            with cd(_support):
                fab_program.run("fab -H myhost basic_run")
            chan.exec_command.assert_called_once_with('nope')

        def comma_separated_string_is_multiple_hosts(self):
            # TODO: requires mock_remote to be capable of multiple distinct
            # connections somehow
            skip()

        def multiple_hosts_works_with_remainder_too(self):
            skip()

        def host_string_shorthand_is_passed_through(self):
            # I.e. is just handed to Connection() as posarg
            skip()
