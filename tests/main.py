"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from invoke.util import cd
from mock import patch
from spec import Spec, assert_contains, skip

from invoke import Context
from fabric.main import program as fab_program

from _util import expect, mock_remote, Session


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

        @mock_remote(Session('myhost', cmd='whoami'))
        def executes_remainder_as_anonymous_task(self, chan):
            # All useful asserts re: host connection & command exec are
            # performed in @mock_remote.
            fab_program.run("fab -H myhost -- whoami", exit=False)

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
        # NOTE: many of these just rely on mock_remote's builtin
        # "channel.exec_command called with given command string" asserts.

        @mock_remote(Session('myhost', cmd='nope'))
        def single_string_is_single_host_and_single_exec(self, chan):
            # In addition to just testing a base case, this checks for a really
            # dumb bug where one appends to, instead of replacing, the task
            # list during parameterization/expansion XD
            with cd(_support):
                fab_program.run("fab -H myhost basic_run")

        @mock_remote(
            Session('host1', cmd='nope'),
            Session('host2', cmd='nope'),
        )
        def comma_separated_string_is_multiple_hosts(self, chan1, chan2):
            with cd(_support):
                fab_program.run("fab -H host1,host2 basic_run")

        @mock_remote(
            Session('host1', cmd='whoami'),
            Session('host2', cmd='whoami'),
        )
        def multiple_hosts_works_with_remainder_too(self, chan1, chan2):
            fab_program.run("fab -H host1,host2 -- whoami")

        @mock_remote(Session(user='someuser', host='host1', port=1234))
        def host_string_shorthand_is_passed_through(self, chan):
            fab_program.run("fab -H someuser@host1:1234 -- whoami")

        class no_hosts_flag_at_all:
            @patch('fabric.main.Context', spec=Context)
            def calls_task_once_with_invoke_context(self, Context):
                with cd(_support):
                    fab_program.run("fab basic_run")
                Context.return_value.run.assert_called_once_with('nope')

            def generates_exception_if_combined_with_remainder(self):
                skip()
