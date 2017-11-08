"""
Tests concerned with the ``fab`` tool & how it overrides Invoke defaults.
"""

import os

from invoke.util import cd
from mock import patch
import pytest # because WHY would you expose @skip normally? -_-
from pytest_relaxed import raises

from fabric.config import Config
from fabric.main import program as fab_program
from fabric.exceptions import NothingToDo

from _util import expect, Session


_support = os.path.join(os.path.dirname(__file__), '_support')
_conf = os.path.abspath(os.path.join(_support, 'config.yml'))


# Crappy helper to inject a test-only runtime config into test invocations.
# TODO: consider e.g. having Invoke grow something like INVOKE_RUNTIME_CONF=xxx
def _run_fab(argstr, **kwargs):
    return fab_program.run("fab -f {} {}".format(_conf, argstr), **kwargs)


class Fab_:
    class core_program_behavior:
        def version_output_contains_our_name_plus_deps(self):
            expect(
                "--version",
                r"""
Fabric .+
Paramiko .+
Invoke .+
""".strip(),
                test='regex'
            )

        def help_output_says_fab(self):
            expect("--help", "Usage: fab", test='contains')

        def exposes_hosts_flag_in_help(self):
            expect("--help", "-H STRING, --hosts=STRING", test='contains')

        def executes_remainder_as_anonymous_task(self, remote):
            remote.expect(host='myhost', cmd='whoami')
            _run_fab("-H myhost -- whoami", exit=False)

        def uses_FABRIC_env_prefix(self, environ):
            environ['FABRIC_RUN_ECHO'] = '1'
            with cd(_support):
                _run_fab("expect-from-env")

    class filenames:
        def loads_fabfile_not_tasks(self):
            "Loads fabfile.py, not tasks.py"
            with cd(_support):
                expect(
                    "--list",
                    """
Available tasks:

  basic-run
  build
  deploy
  expect-from-env
  expect-identities
  expect-identity
  expect-mutation
  expect-mutation-to-fail
  expect-vanilla-Context
  mutate

""".lstrip())

        def loads_fabric_config_files_not_invoke_ones(self):
            for type_ in ('yaml', 'yml', 'json', 'py'):
                with cd(os.path.join(_support, '{}_conf'.format(type_))):
                    # This task, in each subdir, expects data present in a
                    # fabric.<ext> nearby to show up in the config.
                    _run_fab("expect-conf-value")

    class runtime_ssh_config_path:
        def _run(
            self,
            flag='-F',
            file_='ssh_config/runtime.conf',
            tasks='runtime-ssh-config',
        ):
            with cd(_support):
                # Relies on asserts within the task, which will bubble up as
                # it's executed in-process
                cmd = "-c runtime_fabfile {} {} -H runtime {}"
                _run_fab(cmd.format(flag, file_, tasks))

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
        # NOTE: many of these just rely on MockRemote's builtin
        # "channel.exec_command called with given command string" asserts.

        def single_string_is_single_host_and_single_exec(self, remote):
            remote.expect(host='myhost', cmd='nope')
            # In addition to just testing a base case, this checks for a really
            # dumb bug where one appends to, instead of replacing, the task
            # list during parameterization/expansion XD
            with cd(_support):
                _run_fab("-H myhost basic-run")

        def comma_separated_string_is_multiple_hosts(self, remote):
            remote.expect_sessions(
                Session('host1', cmd='nope'),
                Session('host2', cmd='nope'),
            )
            with cd(_support):
                _run_fab("-H host1,host2 basic-run")

        def multiple_hosts_works_with_remainder_too(self, remote):
            remote.expect_sessions(
                Session('host1', cmd='whoami'),
                Session('host2', cmd='whoami'),
            )
            _run_fab("-H host1,host2 -- whoami")

        def host_string_shorthand_is_passed_through(self, remote):
            remote.expect(host='host1', port=1234, user='someuser')
            _run_fab("-H someuser@host1:1234 -- whoami")

        # NOTE: no mocking because no actual run() under test, only
        # parameterization
        # TODO: avoiding for now because implementing this requires more work
        # at the Invoke level re: deciding when to _not_ pass in the
        # session-global config object (Executor's self.config). At the moment,
        # our threading-concurrency API is oriented around Group, and we're not
        # using it for --hosts, so it's not broken...yet.
        @pytest.mark.skip
        def config_mutation_not_preserved(self):
            with cd(_support):
                _run_fab("-H host1,host2 expect-mutation-to-fail")

    class no_hosts_flag:
        def calls_task_once_with_invoke_context(self):
            with cd(_support):
                _run_fab("expect-vanilla-Context")

        @raises(NothingToDo)
        def generates_exception_if_combined_with_remainder(self):
            _run_fab("-- nope")

        def invokelike_multitask_invocation_preserves_config_mutation(self):
            # Mostly a guard against Executor subclass tweaks breaking Invoke
            # behavior added in pyinvoke/invoke#309
            with cd(_support):
                _run_fab("mutate expect-mutation")

    class runtime_identity_file:
        def dash_i_supplies_default_connect_kwarg_key_filename(self):
            # NOTE: the expect-identity task in tests/_support/fabfile.py
            # performs asserts about its context's .connect_kwargs value,
            # relying on other tests to prove connect_kwargs makes its way into
            # that context.
            with cd(_support):
                _run_fab("-i identity.key expect-identity")

        def double_dash_identity_also_works(self):
            with cd(_support):
                _run_fab("--identity identity.key expect-identity")

        def may_be_given_multiple_times(self):
            with cd(_support):
                _run_fab("-i identity.key -i identity2.key expect-identities")
