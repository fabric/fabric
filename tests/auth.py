from getpass import getpass
from pathlib import Path
from unittest.mock import Mock, patch

from invoke.vendor.lexicon import Lexicon
from pytest import raises, fixture
from paramiko import (
    AgentKey,
    AuthFailure,
    InMemoryPrivateKey,
    OnDiskPrivateKey,
    PKey,
    Password,
    SSHConfig,
)

from fabric import Config, OpenSSHAuthStrategy


@fixture(autouse=True)  # under NO circumstances do we wanna talk to an agent
def fake_agent():
    with patch("fabric.auth.Agent") as Agent:
        yield Agent


@fixture
def fake(fake_agent):
    """
    Bag-o-fakes:
    - Agent (do NOT wanna talk to a real one)
    - PKey (do NOT want to load real ones from disk)
    """
    lex = Lexicon()
    lex.Agent = fake_agent
    with patch("fabric.auth.PKey") as PKey:
        lex.PKey = PKey
        yield lex


def _strategy(py_keys=None, ssh_keys=None):
    conf = SSHConfig().lookup("host")
    conf["identityfile"] = ssh_keys or []
    return OpenSSHAuthStrategy(
        ssh_config=conf,
        fabric_config=Config(
            overrides={"authentication": {"identities": py_keys or []}}
        ),
        username="whatever",
    )


class OpenSSHAuthStrategy_:
    def init_accepts_additional_args_and_creates_agent(self, fake):
        with raises(TypeError):
            # Just ssh_config == not good enough
            OpenSSHAuthStrategy(None)
        with raises(TypeError):
            OpenSSHAuthStrategy(None, None)
        ssh_config, fabric_config, username = object(), object(), "foo"
        strat = OpenSSHAuthStrategy(ssh_config, fabric_config, username)
        assert strat.ssh_config is ssh_config
        assert strat.config is fabric_config
        assert strat.username is username
        fake.Agent.assert_called_once_with()
        assert strat.agent is fake.Agent.return_value

    @patch("fabric.auth.partial")
    def get_sources_yields_in_specific_order(self, mock_partial):
        # Yields from get_pubkeys
        strat = _strategy()
        strat.get_pubkeys = Mock(return_value=iter([1, 2, 3]))
        generator = strat.get_sources()
        source = next(generator)
        strat.get_pubkeys.assert_called_once_with()
        assert source == 1
        assert next(generator) == 2
        assert next(generator) == 3
        # Then tries password auth
        pw = next(generator)
        assert isinstance(pw, Password)
        assert pw.username == "whatever"
        getter = pw.password_getter
        assert getter == mock_partial.return_value
        mock_partial.assert_called_once_with(getpass, "whatever's password: ")
        # Safety check
        with raises(StopIteration):
            next(generator)
        # TODO/NOTE: this is, obviously, incomplete!

    def authenticate_always_closes_agent(self):
        strat = _strategy()
        strat.close = Mock()
        oops = Exception("onoz")
        kaboom = Mock(authenticate=Mock(side_effect=oops))
        strat.get_sources = Mock(return_value=iter([kaboom]))
        with raises(AuthFailure):
            strat.authenticate(None)
        strat.close.assert_called_once_with()

    def close_closes_agent(self):
        agent = Mock()
        strat = _strategy()
        strat.agent = agent
        strat.close()
        agent.close.assert_called_once_with()

    class get_pubkeys:
        class fabric_config:
            def loads_identities_config_var(self, fake):
                strat = _strategy(py_keys=["rsa.key"])
                keys = list(strat.get_pubkeys())
                assert len(keys) == 1
                key = keys[0]
                assert isinstance(key, OnDiskPrivateKey)
                fake.PKey.from_path.assert_called_once_with("rsa.key")
                assert key.pkey is fake.PKey.from_path.return_value
                assert key.source == "python-config"
                assert key.path == "rsa.key"

            def silently_skips_nonexistent_files(self, fake):
                key = Mock()
                fake.PKey.from_path.side_effect = [FileNotFoundError, key]
                strat = _strategy(py_keys=["rsa.key", "ed25519.key"])
                keys = list(strat.get_pubkeys())
                assert len(keys) == 1
                assert keys[0].pkey is key
                assert keys[0].path == "ed25519.key"

        class ssh_config:
            def loads_identityfile_key(self, fake):
                strat = _strategy(ssh_keys=["rsa.key"])
                keys = list(strat.get_pubkeys())
                assert len(keys) == 1
                key = keys[0]
                assert isinstance(key, OnDiskPrivateKey)
                fake.PKey.from_path.assert_called_once_with("rsa.key")
                assert key.pkey is fake.PKey.from_path.return_value
                assert key.source == "ssh-config"
                assert key.path == "rsa.key"

            def silently_skips_nonexistent_files(self, fake):
                key = Mock()
                fake.PKey.from_path.side_effect = [FileNotFoundError, key]
                strat = _strategy(ssh_keys=["rsa.key", "ed25519.key"])
                keys = list(strat.get_pubkeys())
                assert len(keys) == 1
                assert keys[0].pkey is key
                assert keys[0].path == "ed25519.key"

        class implicit_user_home_locations:
            def loads_all_four_known_key_types(self, fake):
                strat = _strategy()
                keys = list(strat.get_pubkeys())
                assert [x.path for x in keys] == [
                    Path.home() / ".ssh" / key
                    for key in [
                        "id_rsa",
                        "id_ecdsa",
                        "id_ed25519",
                        "id_dsa",
                    ]
                ]
                assert all(x.source == "implicit-home" for x in keys)

            def silently_skips_nonexistent_files(self, fake):
                fake.PKey.from_path.side_effect = [
                    FileNotFoundError,
                    Mock(),
                    Mock(),
                    Mock(),
                ]
                strat = _strategy()
                keys = list(strat.get_pubkeys())
                assert [x.path for x in keys] == [
                    Path.home() / ".ssh" / key
                    for key in [
                        # "id_rsa",  # not found
                        "id_ecdsa",
                        "id_ed25519",
                        "id_dsa",
                    ]
                ]

            def does_not_load_if_config_based_keys_given(self, fake):
                strat = _strategy(py_keys=["rsa.key"])
                keys = list(strat.get_pubkeys())
                # NOTE: no $HOME keys were loaded by PKey.from_path.
                assert len(keys) == 1
                fake.PKey.from_path.assert_called_once_with("rsa.key")

            @patch("fabric.auth.win32", True)
            def uses_windows_style_ssh_dir_on_windows(self, fake):
                strat = _strategy()
                keys = list(strat.get_pubkeys())
                assert [x.path for x in keys] == [
                    # NOTE: not .ssh, but just ssh
                    Path.home() / "ssh" / key
                    for key in [
                        "id_rsa",
                        "id_ecdsa",
                        "id_ed25519",
                        "id_dsa",
                    ]
                ]

        def loads_keys_from_agent(self, fake):
            # No $HOME keys to gum things up.
            fake.PKey.from_path.side_effect = FileNotFoundError
            agent_keys = [
                AgentKey(fake.Agent.return_value, x)
                for x in (b"dummy", b"data")
            ]
            get_keys = fake.Agent.return_value.get_keys
            get_keys.return_value = agent_keys
            strat = _strategy()
            keys = list(strat.get_pubkeys())
            get_keys.assert_called_once_with()
            assert all(isinstance(x, InMemoryPrivateKey) for x in keys)
            assert [x.pkey for x in keys] == agent_keys

        def yields_sources_in_specific_order(self, fake):
            # Set up fake-enough keys
            # Reminder: 'CLI' in our world generally means
            # CLI-or-Fabric-Config; we inject them via Fabric config.
            class FaKey(PKey):
                def __init__(self, name):
                    self._name = name
                    self.public_blob = None
                    if name.endswith(".cert"):
                        self.public_blob = True  # good enough for AuthStrategy

                @property
                def _fields(self):
                    return [self._name, self.public_blob]

                @property
                def fingerprint(self):
                    return self._name

            # Both a useful lookup source for the fake constructor, and the
            # final expected order of things.
            expected_keys = [
                # Certs, from ssh conf files
                FaKey("ssh-conf.cert"),
                # Certs, from CLI / Python conf files
                FaKey("py-conf.cert"),
                # Agent keys, when overlapping with config file keys
                FaKey("agent-conf.key"),
                # Agent keys, the rest
                FaKey("agent-noconf.key"),
                # Non-cert keys, from the CLI
                FaKey("py-conf.key"),
                # Non-cert keys, from SSH configs
                FaKey("ssh-conf.key"),
            ]

            def get_key(name):
                for candidate in expected_keys:
                    if candidate._name == name:
                        return candidate
                raise Exception(f"Your candidate list has no {name!r}!")

            fake.PKey.from_path.side_effect = get_key
            fake.Agent.return_value.get_keys.return_value = [
                # not also found in config
                get_key("agent-noconf.key"),
                # also found in config, and should show up before agent_noconf
                # does, despite showing up in get_keys() later!
                get_key("agent-conf.key"),
            ]
            strat = _strategy(
                py_keys=["py-conf.key", "py-conf.cert"],
                ssh_keys=["ssh-conf.key", "ssh-conf.cert", "agent-conf.key"],
            )
            keys = list(strat.get_pubkeys())
            # Order check!
            assert [x.pkey for x in keys] == expected_keys
