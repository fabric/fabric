import errno
from os.path import join, expanduser

from paramiko.config import SSHConfig

from fabric import Config
from fabric.util import get_local_user

from mock import patch, call

from _util import support


class Config_:

    def defaults_to_merger_of_global_defaults(self):
        # I.e. our global_defaults + Invoke's global_defaults
        c = Config()
        # From invoke's global_defaults
        assert c.run.warn is False
        # From ours
        assert c.port == 22

    def our_global_defaults_can_override_invokes(self):
        "our global_defaults can override Invoke's key-by-key"
        with patch.object(
            Config,
            "global_defaults",
            return_value={
                "run": {"warn": "nope lol"},
                # NOTE: Config requires these to be present to instantiate
                # happily
                "load_ssh_configs": True,
                "ssh_config_path": None,
            },
        ):
            # If our global_defaults didn't win, this would still
            # resolve to False.
            assert Config().run.warn == "nope lol"

    def has_various_Fabric_specific_default_keys(self):
        c = Config()
        assert c.port == 22
        assert c.user == get_local_user()
        assert c.forward_agent is False
        assert c.connect_kwargs == {}
        assert c.timeouts.connect is None
        assert c.ssh_config_path is None

    def overrides_some_Invoke_defaults(self):
        config = Config()
        # This value defaults to False in Invoke proper.
        assert config.run.replace_env is True
        assert config.tasks.collection_name == "fabfile"

    def uses_Fabric_prefix(self):
        # NOTE: see also the integration-esque tests in tests/main.py; this
        # just tests the underlying data/attribute driving the behavior.
        assert Config().prefix == "fabric"


class ssh_config_loading:
    "ssh_config loading"

    # NOTE: actual _behavior_ of loaded SSH configs is tested in Connection's
    # tests; these tests just prove that the loading itself works & the data is
    # correctly available.

    _system_path = join(support, "ssh_config", "system.conf")
    _user_path = join(support, "ssh_config", "user.conf")
    _runtime_path = join(support, "ssh_config", "runtime.conf")
    _empty_kwargs = dict(
        system_ssh_path="nope/nope/nope", user_ssh_path="nope/noway/nuhuh"
    )

    def defaults_to_empty_sshconfig_obj_if_no_files_found(self):
        c = Config(**self._empty_kwargs)
        # TODO: Currently no great public API that lets us figure out if
        # one of these is 'empty' or not. So for now, expect an empty inner
        # SSHConfig._config from an un-.parse()d such object. (AFAIK, such
        # objects work fine re: .lookup, .get_hostnames etc.)
        assert type(c.base_ssh_config) is SSHConfig
        assert c.base_ssh_config._config == []

    def object_can_be_given_explicitly_via_ssh_config_kwarg(self):
        sc = SSHConfig()
        assert Config(ssh_config=sc).base_ssh_config is sc

    @patch.object(Config, "_load_ssh_file")
    def when_config_obj_given_default_paths_are_not_sought(self, method):
        sc = SSHConfig()
        Config(ssh_config=sc)
        assert not method.called

    @patch.object(Config, "_load_ssh_file")
    def config_obj_prevents_loading_runtime_path_too(self, method):
        sc = SSHConfig()
        Config(ssh_config=sc, runtime_ssh_path=self._system_path)
        assert not method.called

    @patch.object(Config, "_load_ssh_file")
    def when_runtime_path_given_other_paths_are_not_sought(self, method):
        Config(runtime_ssh_path=self._runtime_path)
        method.assert_called_once_with(self._runtime_path)

    @patch.object(Config, "_load_ssh_file")
    def runtime_path_can_be_given_via_config_itself(self, method):
        Config(overrides={"ssh_config_path": self._runtime_path})
        method.assert_called_once_with(self._runtime_path)

    def runtime_path_does_not_die_silently(self):
        try:
            Config(runtime_ssh_path="sure/thing/boss/whatever/you/say")
        except IOError as e:
            assert "No such file or directory" in str(e)
            assert e.errno == errno.ENOENT
        else:
            assert False, "Bad runtime path didn't raise IOError!"

    # TODO: skip on windows
    @patch.object(Config, "_load_ssh_file")
    def default_file_paths_match_openssh(self, method):
        Config()
        method.assert_has_calls(
            [call(expanduser("~/.ssh/config")), call("/etc/ssh/ssh_config")]
        )

    def system_path_loads_ok(self):
        c = Config(
            **dict(self._empty_kwargs, system_ssh_path=self._system_path)
        )
        names = c.base_ssh_config.get_hostnames()
        assert names == {"system", "shared", "*"}

    def user_path_loads_ok(self):
        c = Config(**dict(self._empty_kwargs, user_ssh_path=self._user_path))
        names = c.base_ssh_config.get_hostnames()
        assert names == {"user", "shared", "*"}

    def both_paths_loaded_if_both_exist_with_user_winning(self):
        c = Config(
            user_ssh_path=self._user_path, system_ssh_path=self._system_path
        )
        names = c.base_ssh_config.get_hostnames()
        expected = {"user", "system", "shared", "*"}
        assert names == expected
        # Expect the user value (321), not the system one (123)
        assert c.base_ssh_config.lookup("shared")["port"] == "321"

    @patch.object(Config, "_load_ssh_file")
    @patch("fabric.config.os.path.exists", lambda x: True)
    def runtime_path_subject_to_user_expansion(self, method):
        # TODO: other expansion types? no real need for abspath...
        tilded = "~/probably/not/real/tho"
        Config(runtime_ssh_path=tilded)
        method.assert_called_once_with(expanduser(tilded))

    @patch.object(Config, "_load_ssh_file")
    def user_path_subject_to_user_expansion(self, method):
        # TODO: other expansion types? no real need for abspath...
        tilded = "~/probably/not/real/tho"
        Config(user_ssh_path=tilded)
        method.assert_any_call(expanduser(tilded))

    class core_ssh_load_option_allows_skipping_ssh_config_loading:

        @patch.object(Config, "_load_ssh_file")
        def skips_default_paths(self, method):
            Config(overrides={"load_ssh_configs": False})
            assert not method.called

        @patch.object(Config, "_load_ssh_file")
        def does_not_affect_explicit_object(self, method):
            sc = SSHConfig()
            c = Config(ssh_config=sc, overrides={"load_ssh_configs": False})
            # Implicit loading still doesn't happen...sanity check
            assert not method.called
            # Real test: the obj we passed in is present as usual
            assert c.base_ssh_config is sc

        @patch.object(Config, "_load_ssh_file")
        def does_not_skip_loading_runtime_path(self, method):
            Config(
                runtime_ssh_path=self._runtime_path,
                overrides={"load_ssh_configs": False},
            )
            # Expect that loader method did still run (and, as usual, that
            # it did not load any other files)
            method.assert_called_once_with(self._runtime_path)

    class lazy_loading_and_explicit_methods:

        @patch.object(Config, "_load_ssh_file")
        def may_use_lazy_plus_explicit_methods_to_control_flow(self, method):
            c = Config(lazy=True)
            assert not method.called
            c.set_runtime_ssh_path(self._runtime_path)
            c.load_ssh_config()
            method.assert_called_once_with(self._runtime_path)
