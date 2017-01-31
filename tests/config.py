from os.path import join

from fabric.config import Config
from paramiko.config import SSHConfig

from mock import patch
from spec import Spec, eq_, ok_, skip

from _util import support_path


class Config_(Spec):
    def defaults_to_merger_of_global_defaults(self):
        # I.e. our global_defaults + Invoke's global_defaults
        c = Config()
        # From invoke's global_defaults
        eq_(c.run.warn, False)
        # From ours
        eq_(c.port, 22)

    def has_various_Fabric_specific_default_keys(self):
        # NOTE: Duplicates some other tests but we're now starting to
        # grow options not directly related to user/port stuff, so best
        # to have at least one test listing all expected keys.
        for keyparts in (
            ('port',),
            ('user',),
            ('forward_agent',),
            ('sudo', 'prompt'),
            ('sudo', 'password'),
        ):
            obj = Config()
            for key in keyparts:
                err = "Didn't find expected config key path '{0}'!"
                assert key in obj, err.format(".".join(keyparts))
                obj = obj[key]

    def our_defaults_override_invokes(self):
        "our defaults override invoke's"
        with patch.object(
            Config,
            'global_defaults',
            return_value={
                'run': {'warn': "nope lol"},
                'user': 'me',
                'port': 22,
                'forward_agent': False,
            }
        ):
            # If our global_defaults didn't win, this would still
            # resolve to False.
            eq_(Config().run.warn, "nope lol")

    def we_override_replace_env(self):
        # This value defaults to False in Invoke proper.
        eq_(Config().run.replace_env, True)

    class ssh_config:
        empty_kwargs = dict(
            system_ssh_path='nope/nope/nope',
            user_ssh_path='nope/noway/nuhuh',
        )
        both_kwargs = dict(
            system_ssh_path=join(support_path, 'system.conf'),
            user_ssh_path=join(support_path, 'user.conf'),
        )
        # TODO: wants same 'tweak where the system/user files are sought'
        # behavior as invoke.Config/its tests. Can't literally reuse those
        # prefixes (e.g. it's not /etc/ssh.config but /etc/ssh/ssh_config, and
        # not ~/.ssh_config but ~/.ssh/config) but want same approach so we can
        # just tweak the objects under test instead of mocking open()
        # TODO: ...how does invoke do this integration-wise? ugh. I bet it
        # doesn't
        def defaults_to_empty_sshconfig_obj_if_no_files_found(self):
            c = Config(**self.empty_kwargs)
            # TODO: Currently no great public API that lets us figure out if
            # one of these is 'empty' or not. So for now, expect an empty inner
            # SSHConfig._config with just the initial default glob-rule.
            # NOTE: there's a semi-bug in that NON-empty SSHConfigs can exhibit
            # both the initial empty-glob structure AND a filled-in one (from a
            # real actual 'Host *' entry, if one exists). Doesn't matter for
            # the purposes of this test, but FYI.
            ok_(type(c.base_ssh_config) is SSHConfig)
            eq_(c.base_ssh_config._config, [{'host': ['*'], 'config': {}}])

        def can_be_given_explicitly_via_ssh_kwarg(self):
            sc = SSHConfig()
            ok_(Config(ssh_config=sc).base_ssh_config is sc)

        def when_config_obj_given_default_paths_are_not_sought(self):
            sc = SSHConfig()
            c = Config(ssh_config=sc, **self.both_kwargs)
            # Empty config list -> didn't load the 'user'/'system' hosts from
            # our dummy configs.
            eq_(c.base_ssh_config._config, [])

        def config_obj_prevents_loading_runtime_path_too(self):
            skip()

        def when_runtime_path_given_other_paths_are_not_sought(self):
            skip()

        # TODO: skip on windows
        def default_system_path_is_etc_ssh_ssh_config(self):
            "default system path is /etc/ssh/ssh_config"
            skip()

        def default_user_path_is_HOME_ssh_config(self):
            "default user path is $HOME/.ssh/config"
            skip()

        def system_path_loaded_if_only_file(self):
            skip()

        def user_path_loaded_if_only_file(self):
            skip()

        def both_paths_loaded_if_both_exist(self):
            skip()

        def user_and_system_paths_merge_with_user_winning(self):
            # NOTE: this _mostly_ tests SSHConfig itself, but the order we load
            # them is still highly important, so.
            skip()
