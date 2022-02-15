from itertools import chain, repeat

from io import StringIO

import errno
from os.path import join
import socket
import time

from unittest.mock import patch, Mock, call, ANY
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko import SSHConfig
import pytest  # for mark, internal raises
from pytest import skip, param
from pytest_relaxed import raises
from invoke.vendor.lexicon import Lexicon

from invoke.config import Config as InvokeConfig
from invoke.exceptions import ThreadException

from fabric import Config, Connection
from fabric.exceptions import InvalidV1Env
from fabric.util import get_local_user

from _util import support, faux_v1_env


# Remote is woven in as a config default, so must be patched there
remote_path = "fabric.config.Remote"
remote_shell_path = "fabric.config.RemoteShell"


def _select_result(obj):
    """
    Return iterator/generator suitable for mocking a select.select() call.

    Specifically one that has a single initial return value of ``obj``, and
    then empty results thereafter.

    If ``obj`` is an exception, it will be used as the sole initial
    ``side_effect`` (as opposed to a return value among tuples).
    """
    # select.select() returns three N-tuples. Have it just act like a single
    # read event happened, then quiet after. So chain a single-item iterable to
    # a repeat(). (Mock has no built-in way to do this apparently.)
    initial = [(obj,), tuple(), tuple()]
    if isinstance(obj, Exception) or (
        isinstance(obj, type) and issubclass(obj, Exception)
    ):
        initial = obj
    return chain([initial], repeat([tuple(), tuple(), tuple()]))


class Connection_:
    class basic_attributes:
        def is_connected_defaults_to_False(self):
            assert Connection("host").is_connected is False

        def client_defaults_to_a_new_SSHClient(self):
            c = Connection("host").client
            assert isinstance(c, SSHClient)
            assert c.get_transport() is None

    class known_hosts_behavior:
        def defaults_to_auto_add(self):
            # TODO: change Paramiko API so this isn't a private access
            # TODO: maybe just merge with the __init__ test that is similar
            assert isinstance(Connection("host").client._policy, AutoAddPolicy)

    class init:
        "__init__"

        class host:
            @raises(TypeError)
            def is_required(self):
                Connection()

            def is_exposed_as_attribute(self):
                assert Connection("host").host == "host"  # buffalo buffalo

            def may_contain_user_shorthand(self):
                c = Connection("user@host")
                assert c.host == "host"
                assert c.user == "user"

            def may_contain_port_shorthand(self):
                c = Connection("host:123")
                assert c.host == "host"
                assert c.port == 123

            def may_contain_user_and_port_shorthand(self):
                c = Connection("user@host:123")
                assert c.host == "host"
                assert c.user == "user"
                assert c.port == 123

            def ipv6_addresses_work_ok_but_avoid_port_shorthand(self):
                for addr in ("2001:DB8:0:0:0:0:0:1", "2001:DB8::1", "::1"):
                    c = Connection(addr, port=123)
                    assert c.user == get_local_user()
                    assert c.host == addr
                    assert c.port == 123
                    c2 = Connection("somebody@{}".format(addr), port=123)
                    assert c2.user == "somebody"
                    assert c2.host == addr
                    assert c2.port == 123

        class user:
            def defaults_to_local_user_with_no_config(self):
                # Tautology-tastic!
                assert Connection("host").user == get_local_user()

            def accepts_config_user_option(self):
                config = Config(overrides={"user": "nobody"})
                assert Connection("host", config=config).user == "nobody"

            def may_be_given_as_kwarg(self):
                assert Connection("host", user="somebody").user == "somebody"

            @raises(ValueError)
            def errors_when_given_as_both_kwarg_and_shorthand(self):
                Connection("user@host", user="otheruser")

            def kwarg_wins_over_config(self):
                config = Config(overrides={"user": "nobody"})
                cxn = Connection("host", user="somebody", config=config)
                assert cxn.user == "somebody"

            def shorthand_wins_over_config(self):
                config = Config(overrides={"user": "nobody"})
                cxn = Connection("somebody@host", config=config)
                assert cxn.user == "somebody"

        class port:
            def defaults_to_22_because_yup(self):
                assert Connection("host").port == 22

            def accepts_configuration_port(self):
                config = Config(overrides={"port": 2222})
                assert Connection("host", config=config).port == 2222

            def may_be_given_as_kwarg(self):
                assert Connection("host", port=2202).port == 2202

            @raises(ValueError)
            def errors_when_given_as_both_kwarg_and_shorthand(self):
                Connection("host:123", port=321)

            def kwarg_wins_over_config(self):
                config = Config(overrides={"port": 2222})
                cxn = Connection("host", port=123, config=config)
                assert cxn.port == 123

            def shorthand_wins_over_config(self):
                config = Config(overrides={"port": 2222})
                cxn = Connection("host:123", config=config)
                assert cxn.port == 123

        class forward_agent:
            def defaults_to_False(self):
                assert Connection("host").forward_agent is False

            def accepts_configuration_value(self):
                config = Config(overrides={"forward_agent": True})
                assert Connection("host", config=config).forward_agent is True

            def may_be_given_as_kwarg(self):
                cxn = Connection("host", forward_agent=True)
                assert cxn.forward_agent is True

            def kwarg_wins_over_config(self):
                config = Config(overrides={"forward_agent": True})
                cxn = Connection("host", forward_agent=False, config=config)
                assert cxn.forward_agent is False

        class connect_timeout:
            def defaults_to_None(self):
                assert Connection("host").connect_timeout is None

            def accepts_configuration_value(self):
                config = Config(overrides={"timeouts": {"connect": 10}})
                assert Connection("host", config=config).connect_timeout == 10

            def may_be_given_as_kwarg(self):
                cxn = Connection("host", connect_timeout=15)
                assert cxn.connect_timeout == 15

            def kwarg_wins_over_config(self):
                config = Config(overrides={"timeouts": {"connect": 20}})
                cxn = Connection("host", connect_timeout=100, config=config)
                assert cxn.connect_timeout == 100

        class config:
            # NOTE: behavior local to Config itself is tested in its own test
            # module; below is solely about Connection's config kwarg and its
            # handling of that value

            def is_not_required(self):
                assert Connection("host").config.__class__ == Config

            def can_be_specified(self):
                c = Config(overrides={"user": "me", "custom": "option"})
                config = Connection("host", config=c).config
                assert c is config
                assert config["user"] == "me"
                assert config["custom"] == "option"

            def if_given_an_invoke_Config_we_upgrade_to_our_own_Config(self):
                # Scenario: user has Fabric-level data present at vanilla
                # Invoke config level, and is then creating Connection objects
                # with those vanilla invoke Configs.
                # (Could also _not_ have any Fabric-level data, but then that's
                # just a base case...)
                # TODO: adjust this if we ever switch to all our settings being
                # namespaced...
                vanilla = InvokeConfig(overrides={"forward_agent": True})
                cxn = Connection("host", config=vanilla)
                assert cxn.forward_agent is True  # not False, which is default

        class gateway:
            def is_optional_and_defaults_to_None(self):
                c = Connection(host="host")
                assert c.gateway is None

            def takes_a_Connection(self):
                c = Connection("host", gateway=Connection("otherhost"))
                assert isinstance(c.gateway, Connection)
                assert c.gateway.host == "otherhost"

            def takes_a_string(self):
                c = Connection("host", gateway="meh")
                assert c.gateway == "meh"

            def accepts_configuration_value(self):
                gw = Connection("jumpbox")
                config = Config(overrides={"gateway": gw})
                # TODO: the fact that they will be eq, but _not_ necessarily be
                # the same object, could be problematic in some cases...
                cxn = Connection("host", config=config)
                assert cxn.gateway == gw

        class initializes_client:
            @patch("fabric.connection.SSHClient")
            def instantiates_empty_SSHClient(self, Client):
                Connection("host")
                Client.assert_called_once_with()

            @patch("fabric.connection.AutoAddPolicy")
            def sets_missing_host_key_policy(self, Policy, client):
                # TODO: should make the policy configurable early on
                sentinel = Mock()
                Policy.return_value = sentinel
                Connection("host")
                set_policy = client.set_missing_host_key_policy
                set_policy.assert_called_once_with(sentinel)

            def is_made_available_as_client_attr(self, client):
                # NOTE: client is SSHClient.return_value
                assert Connection("host").client is client

        class ssh_config:
            def _runtime_config(self, overrides=None, basename="runtime"):
                confname = "{}.conf".format(basename)
                runtime_path = join(support, "ssh_config", confname)
                if overrides is None:
                    overrides = {}
                return Config(
                    runtime_ssh_path=runtime_path, overrides=overrides
                )

            def _runtime_cxn(self, **kwargs):
                config = self._runtime_config(**kwargs)
                return Connection("runtime", config=config)

            def effectively_blank_when_no_loaded_config(self):
                c = Config(ssh_config=SSHConfig())
                cxn = Connection("host", config=c)
                # NOTE: paramiko always injects this even if you look up a host
                # that has no rules, even wildcard ones.
                assert cxn.ssh_config == {"hostname": "host"}

            def shows_result_of_lookup_when_loaded_config(self):
                conf = self._runtime_cxn().ssh_config
                expected = {
                    "connecttimeout": "15",
                    "forwardagent": "yes",
                    "hostname": "runtime",
                    "identityfile": ["whatever.key", "some-other.key"],
                    "port": "666",
                    "proxycommand": "my gateway",
                    "user": "abaddon",
                }
                assert conf == expected

            class hostname:
                def original_host_always_set(self):
                    cxn = Connection("somehost")
                    assert cxn.original_host == "somehost"
                    assert cxn.host == "somehost"

                def hostname_directive_overrides_host_attr(self):
                    # TODO: not 100% convinced this is the absolute most
                    # obvious API for 'translation' of given hostname to
                    # ssh-configured hostname, but it feels okay for now.
                    path = join(
                        support, "ssh_config", "overridden_hostname.conf"
                    )
                    config = Config(runtime_ssh_path=path)
                    cxn = Connection("aliasname", config=config)
                    assert cxn.host == "realname"
                    assert cxn.original_host == "aliasname"
                    assert cxn.port == 2222

            class user:
                def wins_over_default(self):
                    assert self._runtime_cxn().user == "abaddon"

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(overrides={"user": "baal"})
                    assert cxn.user == "abaddon"

                def loses_to_explicit(self):
                    # Would be 'abaddon', as above
                    config = self._runtime_config()
                    cxn = Connection("runtime", config=config, user="set")
                    assert cxn.user == "set"

            class port:
                def wins_over_default(self):
                    assert self._runtime_cxn().port == 666

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(overrides={"port": 777})
                    assert cxn.port == 666

                def loses_to_explicit(self):
                    config = self._runtime_config()  # Would be 666, as above
                    cxn = Connection("runtime", config=config, port=777)
                    assert cxn.port == 777

            class forward_agent:
                def wins_over_default(self):
                    assert self._runtime_cxn().forward_agent is True

                def wins_over_configuration(self):
                    # Of course, this "config override" is also the same as the
                    # default. Meh.
                    cxn = self._runtime_cxn(overrides={"forward_agent": False})
                    assert cxn.forward_agent is True

                def loses_to_explicit(self):
                    # Would be True, as above
                    config = self._runtime_config()
                    cxn = Connection(
                        "runtime", config=config, forward_agent=False
                    )
                    assert cxn.forward_agent is False

            class proxy_command:
                def wins_over_default(self):
                    assert self._runtime_cxn().gateway == "my gateway"

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(overrides={"gateway": "meh gw"})
                    assert cxn.gateway == "my gateway"

                def loses_to_explicit(self):
                    # Would be "my gateway", as above
                    config = self._runtime_config()
                    cxn = Connection(
                        "runtime", config=config, gateway="other gateway"
                    )
                    assert cxn.gateway == "other gateway"

                def explicit_False_turns_off_feature(self):
                    # This isn't as necessary for things like user/port, which
                    # _may not_ be None in the end - this setting could be.
                    config = self._runtime_config()
                    cxn = Connection("runtime", config=config, gateway=False)
                    assert cxn.gateway is False

            class proxy_jump:
                def setup(self):
                    self._expected_gw = Connection("jumpuser@jumphost:373")

                def wins_over_default(self):
                    cxn = self._runtime_cxn(basename="proxyjump")
                    assert cxn.gateway == self._expected_gw

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(
                        basename="proxyjump", overrides={"gateway": "meh gw"}
                    )
                    assert cxn.gateway == self._expected_gw

                def loses_to_explicit(self):
                    # Would be a Connection equal to self._expected_gw, as
                    # above
                    config = self._runtime_config(basename="proxyjump")
                    cxn = Connection(
                        "runtime", config=config, gateway="other gateway"
                    )
                    assert cxn.gateway == "other gateway"

                def explicit_False_turns_off_feature(self):
                    config = self._runtime_config(basename="proxyjump")
                    cxn = Connection("runtime", config=config, gateway=False)
                    assert cxn.gateway is False

                def wins_over_proxycommand(self):
                    cxn = self._runtime_cxn(basename="both_proxies")
                    assert cxn.gateway == Connection("winner@everything:777")

                def multi_hop_works_ok(self):
                    cxn = self._runtime_cxn(basename="proxyjump_multi")
                    innermost = cxn.gateway.gateway.gateway
                    middle = cxn.gateway.gateway
                    outermost = cxn.gateway
                    assert innermost == Connection("jumpuser3@jumphost3:411")
                    assert middle == Connection("jumpuser2@jumphost2:872")
                    assert outermost == Connection("jumpuser@jumphost:373")

                def wildcards_do_not_trigger_recursion(self):
                    # When #1850 is present, this will RecursionError.
                    conf = self._runtime_config(basename="proxyjump_recursive")
                    cxn = Connection("runtime.tld", config=conf)
                    assert cxn.gateway == Connection("bastion.tld")
                    assert cxn.gateway.gateway is None

                def multihop_plus_wildcards_still_no_recursion(self):
                    conf = self._runtime_config(
                        basename="proxyjump_multi_recursive"
                    )
                    cxn = Connection("runtime.tld", config=conf)
                    outer = cxn.gateway
                    inner = cxn.gateway.gateway
                    assert outer == Connection("bastion1.tld")
                    assert inner == Connection("bastion2.tld")
                    assert inner.gateway is None

                def gateway_Connections_get_parent_connection_configs(self):
                    conf = self._runtime_config(
                        basename="proxyjump",
                        overrides={"some_random_option": "a-value"},
                    )
                    cxn = Connection("runtime", config=conf)
                    # Sanity
                    assert cxn.config is conf
                    assert cxn.gateway == self._expected_gw
                    # Real check
                    assert cxn.gateway.config.some_random_option == "a-value"
                    # Prove copy not reference
                    # TODO: would we ever WANT a reference? can't imagine...
                    assert cxn.gateway.config is not conf

            class connect_timeout:
                def wins_over_default(self):
                    assert self._runtime_cxn().connect_timeout == 15

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(
                        overrides={"timeouts": {"connect": 17}}
                    )
                    assert cxn.connect_timeout == 15

                def loses_to_explicit(self):
                    config = self._runtime_config()
                    cxn = Connection(
                        "runtime", config=config, connect_timeout=23
                    )
                    assert cxn.connect_timeout == 23

            class identity_file:
                # NOTE: ssh_config value gets merged w/ (instead of overridden
                # by) config and kwarg values; that is tested in the tests for
                # open().
                def basic_loading_of_value(self):
                    # By default, key_filename will be empty, and the data from
                    # the runtime ssh config will be all that appears.
                    value = self._runtime_cxn().connect_kwargs["key_filename"]
                    assert value == ["whatever.key", "some-other.key"]

        class connect_kwargs:
            def defaults_to_empty_dict(self):
                assert Connection("host").connect_kwargs == {}

            def may_be_given_explicitly(self):
                cxn = Connection("host", connect_kwargs={"foo": "bar"})
                assert cxn.connect_kwargs == {"foo": "bar"}

            def may_be_configured(self):
                c = Config(overrides={"connect_kwargs": {"origin": "config"}})
                cxn = Connection("host", config=c)
                assert cxn.connect_kwargs == {"origin": "config"}

            def kwarg_wins_over_config(self):
                # TODO: should this be more of a merge-down?
                c = Config(overrides={"connect_kwargs": {"origin": "config"}})
                cxn = Connection(
                    "host", connect_kwargs={"origin": "kwarg"}, config=c
                )
                assert cxn.connect_kwargs == {"origin": "kwarg"}

        class inline_ssh_env:
            def defaults_to_config_value(self):
                assert Connection("host").inline_ssh_env is True
                config = Config({"inline_ssh_env": False})
                assert (
                    Connection("host", config=config).inline_ssh_env is False
                )

            def may_be_given(self):
                assert Connection("host").inline_ssh_env is True
                cxn = Connection("host", inline_ssh_env=False)
                assert cxn.inline_ssh_env is False

    class from_v1:
        def setup(self):
            self.env = faux_v1_env()

        def _cxn(self, **kwargs):
            self.env.update(kwargs)
            return Connection.from_v1(self.env)

        def must_be_given_explicit_env_arg(self):
            cxn = Connection.from_v1(self.env)
            assert cxn.host == "localghost"

        class obtaining_config:
            @patch("fabric.connection.Config.from_v1")
            def defaults_to_calling_Config_from_v1(self, Config_from_v1):
                Connection.from_v1(self.env)
                Config_from_v1.assert_called_once_with(self.env)

            @patch("fabric.connection.Config.from_v1")
            def may_be_given_config_explicitly(self, Config_from_v1):
                # Arguably a dupe of regular Connection constructor behavior,
                # but whatever.
                Connection.from_v1(env=self.env, config=Config())
                assert not Config_from_v1.called

        class additional_kwargs:
            # I.e. as opposed to what happens to the 'env' kwarg...
            def forwards_arbitrary_kwargs_to_init(self):
                cxn = Connection.from_v1(
                    self.env,
                    connect_kwargs={"foo": "bar"},
                    inline_ssh_env=False,
                    connect_timeout=15,
                )
                assert cxn.connect_kwargs["foo"] == "bar"
                assert cxn.inline_ssh_env is False
                assert cxn.connect_timeout == 15

            def conflicting_kwargs_win_over_v1_env_values(self):
                env = Lexicon(self.env)
                cxn = Connection.from_v1(
                    env, host="not-localghost", port=2222, user="remoteuser"
                )
                assert cxn.host == "not-localghost"
                assert cxn.user == "remoteuser"
                assert cxn.port == 2222

        class var_mappings:
            def host_string(self):
                cxn = self._cxn()  # default is 'localghost'
                assert cxn.host == "localghost"

            @raises(InvalidV1Env)
            def None_host_string_errors_usefully(self):
                self._cxn(host_string=None)

            def user(self):
                cxn = self._cxn(user="space")
                assert cxn.user == "space"

            class port:
                def basic(self):
                    cxn = self._cxn(port=2222)
                    assert cxn.port == 2222

                def casted_to_int(self):
                    cxn = self._cxn(port="2222")
                    assert cxn.port == 2222

                def not_supplied_if_given_in_host_string(self):
                    cxn = self._cxn(host_string="localghost:3737", port=2222)
                    assert cxn.port == 3737

    class string_representation:
        "string representations"

        def str_displays_repr(self):
            c = Connection("meh")
            assert str(c) == "<Connection host=meh>"

        def displays_core_params(self):
            c = Connection(user="me", host="there", port=123)
            template = "<Connection host=there user=me port=123>"
            assert repr(c) == template

        def omits_default_param_values(self):
            c = Connection("justhost")
            assert repr(c) == "<Connection host=justhost>"

        def param_comparison_uses_config(self):
            conf = Config(overrides={"user": "zerocool"})
            c = Connection(
                user="zerocool", host="myhost", port=123, config=conf
            )
            template = "<Connection host=myhost port=123>"
            assert repr(c) == template

        def proxyjump_gateway_shows_type(self):
            c = Connection(host="myhost", gateway=Connection("jump"))
            template = "<Connection host=myhost gw=proxyjump>"
            assert repr(c) == template

        def proxycommand_gateway_shows_type(self):
            c = Connection(host="myhost", gateway="netcat is cool")
            template = "<Connection host=myhost gw=proxycommand>"
            assert repr(c) == template

    class comparison_and_hashing:
        def comparison_uses_host_user_and_port(self):
            # Just host
            assert Connection("host") == Connection("host")
            # Host + user
            c1 = Connection("host", user="foo")
            c2 = Connection("host", user="foo")
            assert c1 == c2
            # Host + user + port
            c1 = Connection("host", user="foo", port=123)
            c2 = Connection("host", user="foo", port=123)
            assert c1 == c2

        def comparison_to_non_Connections_is_False(self):
            assert Connection("host") != 15

        def hashing_works(self):
            assert hash(Connection("host")) == hash(Connection("host"))

        def sorting_works(self):
            # Hostname...
            assert Connection("a-host") < Connection("b-host")
            # User...
            assert Connection("a-host", user="a-user") < Connection(
                "a-host", user="b-user"
            )
            # then port...
            assert Connection("a-host", port=1) < Connection("a-host", port=2)

    class open:
        def has_no_required_args_and_returns_None(self, client):
            assert Connection("host").open() is None

        def calls_SSHClient_connect(self, client):
            "calls paramiko.SSHClient.connect() with correct args"
            Connection("host").open()
            client.connect.assert_called_with(
                username=get_local_user(), hostname="host", port=22
            )

        def passes_through_connect_kwargs(self, client):
            Connection("host", connect_kwargs={"foobar": "bizbaz"}).open()
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname="host",
                port=22,
                foobar="bizbaz",
            )

        def refuses_to_overwrite_connect_kwargs_with_others(self, client):
            for key, value, kwargs in (
                # Core connection args should definitely not get overwritten!
                # NOTE: recall that these keys are the SSHClient.connect()
                # kwarg names, NOT our own config/kwarg names!
                ("hostname", "nothost", {}),
                ("port", 17, {}),
                ("username", "zerocool", {}),
                # These might arguably still be allowed to work, but let's head
                # off confusion anyways.
                ("timeout", 100, {"connect_timeout": 25}),
            ):
                try:
                    Connection(
                        "host", connect_kwargs={key: value}, **kwargs
                    ).open()
                except ValueError as e:
                    err = "Refusing to be ambiguous: connect() kwarg '{}' was given both via regular arg and via connect_kwargs!"  # noqa
                    assert str(e) == err.format(key)
                else:
                    assert False, "Did not raise ValueError!"

        def connect_kwargs_protection_not_tripped_by_defaults(self, client):
            Connection("host", connect_kwargs={"timeout": 300}).open()
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname="host",
                port=22,
                timeout=300,
            )

        def submits_connect_timeout(self, client):
            Connection("host", connect_timeout=27).open()
            client.connect.assert_called_with(
                username=get_local_user(), hostname="host", port=22, timeout=27
            )

        def is_connected_True_when_successful(self, client):
            c = Connection("host")
            c.open()
            assert c.is_connected is True

        def short_circuits_if_already_connected(self, client):
            cxn = Connection("host")
            # First call will set self.transport to fixture's mock
            cxn.open()
            # Second call will check .is_connected which will see active==True,
            # and short circuit
            cxn.open()
            assert client.connect.call_count == 1

        def is_connected_still_False_when_connect_fails(self, client):
            client.connect.side_effect = socket.error
            cxn = Connection("host")
            try:
                cxn.open()
            except socket.error:
                pass
            assert cxn.is_connected is False

        def uses_configured_user_host_and_port(self, client):
            Connection(user="myuser", host="myhost", port=9001).open()
            client.connect.assert_called_once_with(
                username="myuser", hostname="myhost", port=9001
            )

        # NOTE: does more involved stuff so can't use "client" fixture
        @patch("fabric.connection.SSHClient")
        def uses_gateway_channel_as_sock_for_SSHClient_connect(self, Client):
            "uses Connection gateway as 'sock' arg to SSHClient.connect"
            # Setup
            mock_gw = Mock()
            mock_main = Mock()
            Client.side_effect = [mock_gw, mock_main]
            gw = Connection("otherhost")
            gw.open = Mock(wraps=gw.open)
            main = Connection("host", gateway=gw)
            main.open()
            # Expect gateway is also open()'d
            gw.open.assert_called_once_with()
            # Expect direct-tcpip channel open on 1st client
            open_channel = mock_gw.get_transport.return_value.open_channel
            kwargs = open_channel.call_args[1]
            assert kwargs["kind"] == "direct-tcpip"
            assert kwargs["dest_addr"], "host" == 22
            # Expect result of that channel open as sock arg to connect()
            sock_arg = mock_main.connect.call_args[1]["sock"]
            assert sock_arg is open_channel.return_value

        @patch("fabric.connection.ProxyCommand")
        def uses_proxycommand_as_sock_for_Client_connect(self, moxy, client):
            "uses ProxyCommand from gateway as 'sock' arg to SSHClient.connect"
            # Setup
            main = Connection("host", gateway="net catty %h %p")
            main.open()
            # Expect ProxyCommand instantiation
            moxy.assert_called_once_with("net catty host 22")
            # Expect result of that as sock arg to connect()
            sock_arg = client.connect.call_args[1]["sock"]
            assert sock_arg is moxy.return_value

        # TODO: all the various connect-time options such as agent forwarding,
        # host acceptance policies, how to auth, etc etc. These are all aspects
        # of a given session and not necessarily the same for entire lifetime
        # of a Connection object, should it ever disconnect/reconnect.
        # TODO: though some/all of those things might want to be set to
        # defaults at initialization time...

    class connect_kwargs_key_filename:
        "connect_kwargs(key_filename=...)"

        # TODO: it'd be nice to truly separate CLI from regular (non override
        # level) invoke config; as it is, invoke config comes first in expected
        # outputs since otherwise there's no way for --identity to "come
        # first".
        @pytest.mark.parametrize(
            "ssh, invoke, kwarg, expected",
            [
                param(
                    True,
                    True,
                    True,
                    [
                        "configured.key",
                        "kwarg.key",
                        "ssh-config-B.key",
                        "ssh-config-A.key",
                    ],
                    id="All sources",
                ),
                param(
                    True,
                    True,
                    "kwarg.key",
                    [
                        "configured.key",
                        "kwarg.key",
                        "ssh-config-B.key",
                        "ssh-config-A.key",
                    ],
                    id="All sources, kwarg (string)",
                ),
                param(False, False, False, [], id="No sources"),
                param(
                    True,
                    False,
                    False,
                    ["ssh-config-B.key", "ssh-config-A.key"],
                    id="ssh_config only",
                ),
                param(
                    False,
                    True,
                    False,
                    ["configured.key"],
                    id="Invoke-level config only",
                ),
                param(
                    False,
                    False,
                    True,
                    ["kwarg.key"],
                    id="Connection kwarg only",
                ),
                param(
                    False,
                    False,
                    "kwarg.key",
                    ["kwarg.key"],
                    id="Connection kwarg (string) only",
                ),
                param(
                    True,
                    True,
                    False,
                    ["configured.key", "ssh-config-B.key", "ssh-config-A.key"],
                    id="ssh_config + invoke config, no kwarg",
                ),
                param(
                    True,
                    False,
                    True,
                    ["kwarg.key", "ssh-config-B.key", "ssh-config-A.key"],
                    id="ssh_config + kwarg, no Invoke-level config",
                ),
                param(
                    True,
                    False,
                    "kwarg.key",
                    ["kwarg.key", "ssh-config-B.key", "ssh-config-A.key"],
                    id="ssh_config + kwarg (string), no Invoke-level config",
                ),
                param(
                    False,
                    True,
                    True,
                    ["configured.key", "kwarg.key"],
                    id="Invoke-level config + kwarg, no ssh_config",
                ),
                param(
                    False,
                    True,
                    "kwarg.key",
                    ["configured.key", "kwarg.key"],
                    id="Invoke-level config + kwarg (string), no ssh_config",
                ),
                param(
                    True,
                    "string.key",
                    False,
                    ["string.key", "ssh-config-B.key", "ssh-config-A.key"],
                    id="ssh_config, string Invoke config, no kwarg",
                ),
                param(
                    False,
                    "string.key",
                    True,
                    ["string.key", "kwarg.key"],
                    id="no ssh_config, string Invoke config, list kwarg",
                ),
                param(
                    False,
                    "config.key",
                    "kwarg.key",
                    ["config.key", "kwarg.key"],
                    id="no ssh_config, string Invoke config, string kwarg",
                ),
                param(
                    True,
                    "config.key",
                    "kwarg.key",
                    [
                        "config.key",
                        "kwarg.key",
                        "ssh-config-B.key",
                        "ssh-config-A.key",
                    ],
                    id="ssh_config, string Invoke config, string kwarg",
                ),
            ],
        )
        def merges_sources(self, client, ssh, invoke, kwarg, expected):
            config_kwargs = {}
            if ssh:
                # SSH config with 2x IdentityFile directives.
                config_kwargs["runtime_ssh_path"] = join(
                    support, "ssh_config", "runtime_identity.conf"
                )
            if invoke:
                # Assume string value if not literal True
                value = ["configured.key"] if invoke is True else invoke
                # Use overrides config level to mimic --identity use NOTE: (the
                # fact that --identity is an override, and thus overrides eg
                # invoke config file values is part of invoke's config test
                # suite)
                config_kwargs["overrides"] = {
                    "connect_kwargs": {"key_filename": value}
                }
            conf = Config(**config_kwargs)
            connect_kwargs = {}
            if kwarg:
                # Assume string value if not literal True
                value = ["kwarg.key"] if kwarg is True else kwarg
                connect_kwargs = {"key_filename": value}

            # Tie in all sources that were configured & open()
            Connection(
                "runtime", config=conf, connect_kwargs=connect_kwargs
            ).open()
            # Ensure we got the expected list of keys
            kwargs = client.connect.call_args[1]
            if expected:
                assert kwargs["key_filename"] == expected
            else:
                # No key filenames -> it's not even passed in as connect_kwargs
                # is gonna be a blank dict
                assert "key_filename" not in kwargs

    class close:
        def has_no_required_args_and_returns_None(self, client):
            c = Connection("host")
            c.open()
            assert c.close() is None

        def calls_SSHClient_close(self, client):
            "calls paramiko.SSHClient.close()"
            c = Connection("host")
            c.open()
            c.close()
            client.close.assert_called_with()

        def calls_SFTPClient_close(self, client):
            "calls paramiko.SFTPClient.close()"
            c = Connection("host")
            c.open()
            sftp_client = c.sftp()
            assert c._sftp is not None
            c.close()
            assert c._sftp is None
            sftp_client.close.assert_called_with()

        def calls_SFTPClient_close_not_called_if_not_open(self, client):
            "calls paramiko.SFTPClient.close()"
            c = Connection("host")
            c.open()
            assert c._sftp is None
            c.close()
            assert c._sftp is None

        @patch("fabric.connection.AgentRequestHandler")
        def calls_agent_handler_close_if_enabled(self, Handler, client):
            c = Connection("host", forward_agent=True)
            c.create_session()
            c.close()
            # NOTE: this will need to change if, for w/e reason, we ever want
            # to run multiple handlers at once
            Handler.return_value.close.assert_called_once_with()

        def short_circuits_if_not_connected(self, client):
            c = Connection("host")
            # Won't trigger close() on client because it'll already think it's
            # closed (due to no .transport & the behavior of .is_connected)
            c.close()
            assert not client.close.called

        def class_works_as_a_closing_contextmanager(self, client):
            with Connection("host") as c:
                c.open()
            client.close.assert_called_once_with()

    class create_session:
        def calls_open_for_you(self, client):
            c = Connection("host")
            c.open = Mock()
            c.transport = Mock()  # so create_session no asplode
            c.create_session()
            assert c.open.called

        @patch("fabric.connection.AgentRequestHandler")
        def activates_paramiko_agent_forwarding_if_configured(
            self, Handler, client
        ):
            c = Connection("host", forward_agent=True)
            chan = c.create_session()
            Handler.assert_called_once_with(chan)

    class run:
        # NOTE: most actual run related tests live in the runners module's
        # tests. Here we are just testing the outer interface a bit.

        @patch(remote_path)
        def calls_open_for_you(self, Remote, client):
            c = Connection("host")
            c.open = Mock()
            c.run("command")
            assert c.open.called

        @patch(remote_path)
        def passes_inline_env_to_Remote(self, Remote, client):
            Connection("host").run("command")
            assert Remote.call_args[1]["inline_env"] is True
            Connection("host", inline_ssh_env=False).run("command")
            assert Remote.call_args[1]["inline_env"] is False

        @patch(remote_path)
        def calls_Remote_run_with_command_and_kwargs_and_returns_its_result(
            self, Remote, client
        ):
            remote = Remote.return_value
            c = Connection("host")
            r1 = c.run("command")
            r2 = c.run("command", warn=True, hide="stderr")
            # NOTE: somehow, .call_args & the methods built on it (like
            # .assert_called_with()) stopped working, apparently triggered by
            # our code...somehow...after commit (roughly) 80906c7.
            # And yet, .call_args_list and its brethren work fine. Wha?
            Remote.assert_any_call(context=c, inline_env=True)
            remote.run.assert_has_calls(
                [call("command"), call("command", warn=True, hide="stderr")]
            )
            for r in (r1, r2):
                assert r is remote.run.return_value

    class shell:
        def setup(self):
            self.defaults = Config.global_defaults()["run"]

        @patch(remote_shell_path)
        def calls_RemoteShell_run_with_all_kwargs_and_returns_its_result(
            self, RemoteShell, client
        ):
            remote = RemoteShell.return_value
            cxn = Connection("host")
            kwargs = dict(
                env={"foo": "bar"},
                replace_env=True,
                encoding="utf-16",
                in_stream=StringIO("meh"),
                watchers=["meh"],
            )
            result = cxn.shell(**kwargs)
            RemoteShell.assert_any_call(context=cxn)
            assert remote.run.call_count == 1
            # Expect explicit use of default values for all kwarg-settings
            # besides what shell() itself tweaks
            expected = dict(self.defaults, pty=True, command=None, **kwargs)
            assert remote.run.call_args[1] == expected
            assert result is remote.run.return_value

        def raises_TypeError_for_disallowed_kwargs(self, client):
            for key in self.defaults.keys():
                if key in (
                    "env",
                    "replace_env",
                    "encoding",
                    "in_stream",
                    "watchers",
                ):
                    continue
                with pytest.raises(
                    TypeError,
                    match=r"unexpected keyword arguments: \['{}'\]".format(
                        key
                    ),
                ):
                    Connection("host").shell(**{key: "whatever"})

        @patch(remote_shell_path)
        def honors_config_system_for_allowed_kwargs(self, RemoteShell, client):
            remote = RemoteShell.return_value
            allowed = dict(
                env={"foo": "bar"},
                replace_env=True,
                encoding="utf-16",
                in_stream="sentinel",
                watchers=["sentinel"],
            )
            ignored = dict(echo=True, hide="foo")  # Spot check
            config = Config({"run": dict(allowed, **ignored)})
            cxn = Connection("host", config=config)
            cxn.shell()
            kwargs = remote.run.call_args[1]
            for key, value in allowed.items():
                assert kwargs[key] == value
            for key, value in ignored.items():
                assert kwargs[key] == self.defaults[key]

    class local:
        # NOTE: most tests for this functionality live in Invoke's runner
        # tests.
        @patch("invoke.config.Local")
        def calls_invoke_Local_run(self, Local):
            Connection("host").local("foo")
            # NOTE: yet another casualty of the bizarre mock issues
            assert call().run("foo") in Local.mock_calls

    class sudo:
        @patch(remote_path)
        def calls_open_for_you(self, Remote, client):
            c = Connection("host")
            c.open = Mock()
            c.sudo("command")
            assert c.open.called

        @patch(remote_path)
        def passes_inline_env_to_Remote(self, Remote, client):
            Connection("host").sudo("command")
            assert Remote.call_args[1]["inline_env"] is True
            Connection("host", inline_ssh_env=False).sudo("command")
            assert Remote.call_args[1]["inline_env"] is False

        @patch(remote_path)
        def basic_invocation(self, Remote, client):
            # Technically duplicates Invoke-level tests, but ensures things
            # still work correctly at our level.
            cxn = Connection("host")
            cxn.sudo("foo")
            cmd = "sudo -S -p '{}' foo".format(cxn.config.sudo.prompt)
            # NOTE: this is another spot where Mock.call_args is inexplicably
            # None despite call_args_list being populated. WTF. (Also,
            # Remote.return_value is two different Mocks now, despite Remote's
            # own Mock having the same ID here and in code under test. WTF!!)
            expected = [
                call(context=cxn, inline_env=True),
                call().run(cmd, watchers=ANY),
            ]
            assert Remote.mock_calls == expected
            # NOTE: we used to have a "sudo return value is literally the same
            # return value from Remote.run()" sanity check here, which is
            # completely impossible now thanks to the above issue.

        def per_host_password_works_as_expected(self):
            # TODO: needs clearly defined "per-host" config API, if a distinct
            # one is necessary besides "the config obj handed in when
            # instantiating the Connection".
            # E.g. generate a Connection pulling in a sudo.password value from
            # what would be a generic conf file or similar, *and* one more
            # specific to that particular Connection (perhaps simply the
            # 'override' level?), w/ test asserting the more-specific value is
            # what's submitted.
            skip()

    class sftp:
        def returns_result_of_client_open_sftp(self, client):
            "returns result of client.open_sftp()"
            sentinel = object()
            client.open_sftp.return_value = sentinel
            assert Connection("host").sftp() == sentinel
            client.open_sftp.assert_called_with()

        def lazily_caches_result(self, client):
            sentinel1, sentinel2 = object(), object()
            client.open_sftp.side_effect = [sentinel1, sentinel2]
            cxn = Connection("host")
            first = cxn.sftp()
            # TODO: why aren't we just asserting about calls of open_sftp???
            err = "{0!r} wasn't the sentinel object()!"
            assert first is sentinel1, err.format(first)
            second = cxn.sftp()
            assert second is sentinel1, err.format(second)

    class get:
        @patch("fabric.connection.Transfer")
        def calls_Transfer_get(self, Transfer):
            "calls Transfer.get()"
            c = Connection("host")
            c.get("meh")
            Transfer.assert_called_with(c)
            Transfer.return_value.get.assert_called_with("meh")

    class put:
        @patch("fabric.connection.Transfer")
        def calls_Transfer_put(self, Transfer):
            "calls Transfer.put()"
            c = Connection("host")
            c.put("meh")
            Transfer.assert_called_with(c)
            Transfer.return_value.put.assert_called_with("meh")

    class forward_local:
        @patch("fabric.tunnels.select")
        @patch("fabric.tunnels.socket.socket")
        @patch("fabric.connection.SSHClient")
        def _forward_local(self, kwargs, Client, mocket, select):
            # Tease out bits of kwargs for use in the mocking/expecting.
            # But leave it alone for raw passthru to the API call itself.
            # TODO: unhappy with how much this apes the real code & its sig...
            local_port = kwargs["local_port"]
            remote_port = kwargs.get("remote_port", local_port)
            local_host = kwargs.get("local_host", "localhost")
            remote_host = kwargs.get("remote_host", "localhost")
            # These aren't part of the real sig, but this is easier than trying
            # to reconcile the mock decorators + optional-value kwargs. meh.
            tunnel_exception = kwargs.pop("tunnel_exception", None)
            listener_exception = kwargs.pop("listener_exception", False)
            # Mock setup
            client = Client.return_value
            listener_sock = Mock(name="listener_sock")
            if listener_exception:
                listener_sock.bind.side_effect = listener_exception
            data = "Some data".encode()
            tunnel_sock = Mock(name="tunnel_sock", recv=lambda n: data)
            local_addr = Mock()
            transport = client.get_transport.return_value
            channel = transport.open_channel.return_value
            # socket.socket is only called once directly
            mocket.return_value = listener_sock
            # The 2nd socket is obtained via an accept() (which should only
            # fire once & raise EAGAIN after)
            listener_sock.accept.side_effect = chain(
                [(tunnel_sock, local_addr)],
                # TODO: should this become BlockingIOError too?
                repeat(socket.error(errno.EAGAIN, "nothing yet")),
            )
            obj = tunnel_sock if tunnel_exception is None else tunnel_exception
            select.select.side_effect = _select_result(obj)
            with Connection("host").forward_local(**kwargs):
                # Make sure we give listener thread enough time to boot up :(
                # Otherwise we might assert before it does things. (NOTE:
                # doesn't need to be much, even at 0.01s, 0/100 trials failed
                # (vs 45/100 with no sleep)
                time.sleep(0.015)
                assert client.connect.call_args[1]["hostname"] == "host"
                listener_sock.setsockopt.assert_called_once_with(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
                )
                listener_sock.setblocking.assert_called_once_with(0)
                listener_sock.bind.assert_called_once_with(
                    (local_host, local_port)
                )
                if not listener_exception:
                    listener_sock.listen.assert_called_once_with(1)
                    transport.open_channel.assert_called_once_with(
                        "direct-tcpip", (remote_host, remote_port), local_addr
                    )
                # Local write to tunnel_sock is implied by its mocked-out
                # recv() call above...
                # NOTE: don't assert if explodey; we want to mimic "the only
                # error that occurred was within the thread" behavior being
                # tested by thread-exception-handling tests
                if not (tunnel_exception or listener_exception):
                    channel.sendall.assert_called_once_with(data)
            # Shutdown, with another sleep because threads.
            time.sleep(0.015)
            if not listener_exception:
                tunnel_sock.close.assert_called_once_with()
                channel.close.assert_called_once_with()
                listener_sock.close.assert_called_once_with()

        def forwards_local_port_to_remote_end(self):
            self._forward_local({"local_port": 1234})

        def distinct_remote_port(self):
            self._forward_local({"local_port": 1234, "remote_port": 4321})

        def non_localhost_listener(self):
            self._forward_local(
                {"local_port": 1234, "local_host": "nearby_local_host"}
            )

        def non_remote_localhost_connection(self):
            self._forward_local(
                {"local_port": 1234, "remote_host": "nearby_remote_host"}
            )

        def _thread_error(self, which):
            class Sentinel(Exception):
                pass

            try:
                self._forward_local(
                    {
                        "local_port": 1234,
                        "{}_exception".format(which): Sentinel,
                    }
                )
            except ThreadException as e:
                # NOTE: ensures that we're getting what we expected and not
                # some deeper, test-bug related error
                assert len(e.exceptions) == 1
                inner = e.exceptions[0]
                err = "Expected wrapped exception to be Sentinel, was {}"
                assert inner.type is Sentinel, err.format(inner.type.__name__)
            else:
                # no exception happened :( implies the thread went boom but
                # nobody noticed
                err = "Failed to get ThreadException on {} error"
                assert False, err.format(which)

        def tunnel_errors_bubble_up(self):
            self._thread_error("tunnel")

        def tunnel_manager_errors_bubble_up(self):
            self._thread_error("listener")

        # TODO: these require additional refactoring of _forward_local to be
        # more like the decorators in _util
        def multiple_tunnels_can_be_open_at_once(self):
            skip()

    class forward_remote:
        @patch("fabric.connection.socket.socket")
        @patch("fabric.tunnels.select")
        @patch("fabric.connection.SSHClient")
        def _forward_remote(self, kwargs, Client, select, mocket):
            # TODO: unhappy with how much this duplicates of the code under
            # test, re: sig/default vals
            # Set up parameter values/defaults
            remote_port = kwargs["remote_port"]
            remote_host = kwargs.get("remote_host", "127.0.0.1")
            local_port = kwargs.get("local_port", remote_port)
            local_host = kwargs.get("local_host", "localhost")
            # Mock/etc setup, anything that can be prepped before the forward
            # occurs (which is most things)
            tun_socket = mocket.return_value
            cxn = Connection("host")
            # Channel that will yield data when read from
            chan = Mock()
            chan.recv.return_value = "data"
            # And make select() yield it as being ready once, when called
            select.select.side_effect = _select_result(chan)
            with cxn.forward_remote(**kwargs):
                # At this point Connection.open() has run and generated a
                # Transport mock for us (because SSHClient is mocked). Let's
                # first make sure we asked it for the port forward...
                # NOTE: this feels like it's too limited/tautological a test,
                # until you realize that it's functionally impossible to mock
                # out everything required for Paramiko's inner guts to run
                # _parse_channel_open() and suchlike :(
                call = cxn.transport.request_port_forward.call_args_list[0]
                assert call[1]["address"] == remote_host
                assert call[1]["port"] == remote_port
                # Pretend the Transport called our callback with mock Channel
                call[1]["handler"](chan, tuple(), tuple())
                # Then have to sleep a bit to make sure we give the tunnel
                # created by that callback to spin up; otherwise ~5% of the
                # time we exit the contextmanager so fast, the tunnel's "you're
                # done!" flag is set before it even gets a chance to select()
                # once.
                time.sleep(0.01)
                # And make sure we hooked up to the local socket OK
                tup = (local_host, local_port)
                tun_socket.connect.assert_called_once_with(tup)
            # Expect that our socket got written to by the tunnel (due to the
            # above-setup select() and channel mocking). Need to do this after
            # tunnel shutdown or we risk thread ordering issues.
            tun_socket.sendall.assert_called_once_with("data")
            # Ensure we closed down the mock socket
            mocket.return_value.close.assert_called_once_with()
            # And that the transport canceled the port forward on the remote
            # end.
            assert cxn.transport.cancel_port_forward.call_count == 1

        def forwards_remote_port_to_local_end(self):
            self._forward_remote({"remote_port": 1234})

        def distinct_local_port(self):
            self._forward_remote({"remote_port": 1234, "local_port": 4321})

        def non_localhost_connections(self):
            self._forward_remote(
                {"remote_port": 1234, "local_host": "nearby_local_host"}
            )

        def remote_non_localhost_listener(self):
            self._forward_remote(
                {"remote_port": 1234, "remote_host": "192.168.1.254"}
            )

        # TODO: these require additional refactoring of _forward_remote to be
        # more like the decorators in _util
        def multiple_tunnels_can_be_open_at_once(self):
            skip()

        def tunnel_errors_bubble_up(self):
            skip()

        def listener_errors_bubble_up(self):
            skip()
