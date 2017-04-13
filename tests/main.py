"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from invoke.util import cd
from mock import patch
from spec import Spec, assert_contains, raises, skip

from fabric.config import Config
from fabric.main import program as fab_program
from fabric.exceptions import NothingToDo

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

        def uses_FABRIC_env_prefix(self):
            # NOTE: see also the more unit-y tests in tests/config.py
            assert False

    class filenames:
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
  expect_mutation
  expect_mutation_to_fail
  expect_vanilla_Context
  mutate

""".lstrip())

        def loads_fabric_config_files_not_invoke_ones(self):
            # NOTE: see also the more unit-y tests in tests/config.py
            for type_ in ('yaml', 'json', 'py'):
                with cd(os.path.join(_support, '{}_conf'.format(type_))):
                    fab_program.run("fab expect_conf_value")

    class runtime_ssh_config_path:
        def _run(
            self,
            flag='-F',
            file_='ssh_config/runtime.conf',
            tasks='runtime_ssh_config',
        ):
            with cd(_support):
                # Relies on asserts within the task, which will bubble up as
                # it's executed in-process
                cmd = "fab -c runtime_fabfile {} {} -H runtime {}"
                fab_program.run(cmd.format(flag, file_, tasks))

        def capital_F_flag_specifies_runtime_ssh_config_file(self):
            self._run(flag='-F')

        def long_form_flag_also_works(self):
            self._run(flag='--ssh-config')

        @raises(IOError)
        def IOErrors_if_given_missing_file(self):
            self._run(file_='nope/nothere.conf')

        @patch.object(Config, '_load_ssh_file')
        def config_only_loaded_once_per_session(self, method):
            # Task that doesn't make assertions about the config (since the
            # _actual_ config it gets is empty as we had to mock out the loader
            # method...sigh)
            self._run(tasks='dummy dummy')
            # Called only once (initial __init__) with runtime conf, instead of
            # that plus a few more pairs of calls against the default files
            # (which is what happens when clone() isn't preserving the
            # already-parsed/loaded SSHConfig)
            method.assert_called_once_with('ssh_config/runtime.conf')

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

        # NOTE: no mocking because no actual run() under test, only
        # parameterization
        def config_mutation_not_preserved(self):
            # TODO: avoiding for now because implementing this requires more
            # work at the Invoke level re: deciding when to _not_ pass in the
            # session-global config object (Executor's self.config). At the
            # moment, our threading-concurrency API is oriented around Group,
            # and we're not using it for --hosts, so it's not broken...yet.
            skip()
            with cd(_support):
                fab_program.run("fab -H host1,host2 expect_mutation_to_fail")

    class no_hosts_flag:
        def calls_task_once_with_invoke_context(self):
            with cd(_support):
                fab_program.run("fab expect_vanilla_Context")

        @raises(NothingToDo)
        def generates_exception_if_combined_with_remainder(self):
            fab_program.run("fab -- nope")

        def invokelike_multitask_invocation_preserves_config_mutation(self):
            # Mostly a guard against Executor subclass tweaks breaking Invoke
            # behavior added in pyinvoke/invoke#309
            with cd(_support):
                fab_program.run("fab mutate expect_mutation")
