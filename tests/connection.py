from itertools import chain, repeat
from invoke.vendor.six import b
import errno
from os.path import join
import socket
import time

from spec import Spec, eq_, raises, ok_, skip
from mock import patch, Mock, call, PropertyMock, ANY
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko import SSHConfig

from invoke.config import Config as InvokeConfig
from invoke.exceptions import ThreadException

from fabric.connection import Connection, Config
from fabric.util import get_local_user

from _util import support_path


# Remote is woven in as a config default, so must be patched there
remote_path = 'fabric.config.Remote'


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
    if (
        isinstance(obj, Exception)
        or (isinstance(obj, type) and issubclass(obj, Exception))
    ):
        initial = obj
    return chain([initial], repeat([tuple(), tuple(), tuple()]))


class Connection_(Spec):
    class basic_attributes:
        def is_connected_defaults_to_False(self):
            eq_(Connection('host').is_connected, False)

        def client_defaults_to_a_new_SSHClient(self):
            c = Connection('host').client
            ok_(isinstance(c, SSHClient))
            eq_(c.get_transport(), None)

    class known_hosts_behavior:
        def defaults_to_auto_add(self):
            # TODO: change Paramiko API so this isn't a private access
            # TODO: maybe just merge with the __init__ test that is similar
            ok_(isinstance(Connection('host').client._policy, AutoAddPolicy))

    class init:
        "__init__"

        class host:
            @raises(TypeError)
            def is_required(self):
                Connection()

            def is_exposed_as_attribute(self):
                eq_(Connection('host').host, 'host') # buffalo buffalo

            def may_contain_user_shorthand(self):
                c = Connection('user@host')
                eq_(c.host, 'host')
                eq_(c.user, 'user')

            def may_contain_port_shorthand(self):
                c = Connection('host:123')
                eq_(c.host, 'host')
                eq_(c.port, 123)

            def may_contain_user_and_port_shorthand(self):
                c = Connection('user@host:123')
                eq_(c.host, 'host')
                eq_(c.user, 'user')
                eq_(c.port, 123)

            def ipv6_addresses_work_ok_but_avoid_port_shorthand(self):
                for addr in (
                    '2001:DB8:0:0:0:0:0:1',
                    '2001:DB8::1',
                    '::1',
                ):
                    c = Connection(addr, port=123)
                    eq_(c.user, get_local_user())
                    eq_(c.host, addr)
                    eq_(c.port, 123)
                    c2 = Connection("somebody@{0}".format(addr), port=123)
                    eq_(c2.user, "somebody")
                    eq_(c2.host, addr)
                    eq_(c2.port, 123)

        class user:
            def defaults_to_local_user_with_no_config(self):
                # Tautology-tastic!
                eq_(Connection('host').user, get_local_user())

            def accepts_config_user_option(self):
                config = Config(overrides={'user': 'nobody'})
                eq_(Connection('host', config=config).user, 'nobody')

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', user='somebody').user, 'somebody')

            @raises(ValueError)
            def errors_when_given_as_both_kwarg_and_shorthand(self):
                Connection('user@host', user='otheruser')

            def kwarg_wins_over_config(self):
                config = Config(overrides={'user': 'nobody'})
                eq_(
                    Connection('host', user='somebody', config=config).user,
                    'somebody'
                )

            def shorthand_wins_over_config(self):
                config = Config(overrides={'user': 'nobody'})
                eq_(
                    Connection('somebody@host', config=config).user,
                    'somebody'
                )

        class port:
            def defaults_to_22_because_yup(self):
                eq_(Connection('host').port, 22)

            def accepts_configuration_port(self):
                config = Config(overrides={'port': 2222})
                eq_(Connection('host', config=config).port, 2222)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', port=2202).port, 2202)

            @raises(ValueError)
            def errors_when_given_as_both_kwarg_and_shorthand(self):
                Connection('host:123', port=321)

            def kwarg_wins_over_config(self):
                config = Config(overrides={'port': 2222})
                eq_(
                    Connection('host', port=123, config=config).port,
                    123
                )

            def shorthand_wins_over_config(self):
                config = Config(overrides={'port': 2222})
                eq_(
                    Connection('host:123', config=config).port,
                    123
                )

        class forward_agent:
            def defaults_to_False(self):
                eq_(Connection('host').forward_agent, False)

            def accepts_configuration_value(self):
                config = Config(overrides={
                    'forward_agent': True,
                    'load_ssh_configs': False,
                })
                eq_(Connection('host', config=config).forward_agent, True)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', forward_agent=True).forward_agent, True)

            def kwarg_wins_over_config(self):
                config = Config(overrides={'forward_agent': True})
                cxn = Connection('host', forward_agent=False, config=config)
                eq_(cxn.forward_agent, False)

        class connect_timeout:
            def defaults_to_None(self):
                eq_(Connection('host').connect_timeout, None)

            def accepts_configuration_value(self):
                config = Config(overrides={
                    'timeouts': {'connect': 10},
                    'load_ssh_configs': False,
                })
                eq_(Connection('host', config=config).connect_timeout, 10)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', connect_timeout=15).connect_timeout, 15)

            def kwarg_wins_over_config(self):
                config = Config(overrides={'timeouts': {'connect': 20}})
                cxn = Connection('host', connect_timeout=100, config=config)
                eq_(cxn.connect_timeout, 100)

        class config:
            # NOTE: behavior local to Config itself is tested in its own test
            # module; below is solely about Connection's config kwarg and its
            # handling of that value

            def is_not_required(self):
                eq_(Connection('host').config.__class__, Config)

            def can_be_specified(self):
                c = Config(overrides={'user': 'me', 'custom': 'option'})
                config = Connection('host', config=c).config
                ok_(c is config)
                eq_(config['user'], 'me')
                eq_(config['custom'], 'option')

            def if_given_an_invoke_Config_we_upgrade_to_our_own_Config(self):
                # Scenario: user has Fabric-level data present at vanilla
                # Invoke config level, and is then creating Connection objects
                # with those vanilla invoke Configs.
                # (Could also _not_ have any Fabric-level data, but then that's
                # just a base case...)
                # TODO: adjust this if we ever switch to all our settings being
                # namespaced...
                vanilla = InvokeConfig(overrides={
                    'forward_agent': True,
                    'load_ssh_configs': False,
                })
                cxn = Connection('host', config=vanilla)
                eq_(cxn.forward_agent, True) # not False, which is default

        class gateway:
            def is_optional_and_defaults_to_None(self):
                c = Connection(host='host')
                eq_(c.gateway, None)

            def takes_a_Connection(self):
                c = Connection('host', gateway=Connection('otherhost'))
                ok_(isinstance(c.gateway, Connection))
                eq_(c.gateway.host, 'otherhost')

            def takes_a_string(self):
                c = Connection('host', gateway="meh")
                eq_(c.gateway, "meh")

            def accepts_configuration_value(self):
                gw = Connection('jumpbox')
                config = Config(overrides={
                    'gateway': gw,
                    'load_ssh_configs': False,
                })
                # TODO: the fact that they will be eq, but _not_ necessarily be
                # the same object, could be problematic in some cases...
                cxn = Connection('host', config=config)
                eq_(cxn.gateway, gw)

        class initializes_client:
            @patch('fabric.connection.SSHClient')
            def instantiates_empty_SSHClient(self, Client):
                Connection('host')
                Client.assert_called_once_with()

            @patch('fabric.connection.SSHClient')
            @patch('fabric.connection.AutoAddPolicy')
            def sets_missing_host_key_policy(self, Policy, Client):
                # TODO: should make the policy configurable early on
                sentinel = Mock()
                Policy.return_value = sentinel
                Connection('host')
                set_policy = Client.return_value.set_missing_host_key_policy
                set_policy.assert_called_once_with(sentinel)

            @patch('fabric.connection.SSHClient')
            def is_made_available_as_client_attr(self, Client):
                sentinel = Mock()
                Client.return_value = sentinel
                ok_(Connection('host').client is sentinel)

        class ssh_config:
            def _runtime_config(self, overrides=None, basename='runtime'):
                confname = "{0}.conf".format(basename)
                runtime_path = join(support_path, 'ssh_config', confname)
                if overrides is None:
                    overrides = {}
                return Config(
                    runtime_ssh_path=runtime_path,
                    overrides=overrides,
                )

            def _runtime_cxn(self, **kwargs):
                config = self._runtime_config(**kwargs)
                return Connection('runtime', config=config)

            def effectively_blank_when_no_loaded_config(self):
                c = Config(ssh_config=SSHConfig())
                eq_(
                    Connection('host', config=c).ssh_config,
                    # NOTE: paramiko always injects this even if you look up a
                    # host that has no rules, even wildcard ones.
                    {'hostname': 'host'},
                )

            def shows_result_of_lookup_when_loaded_config(self):
                eq_(
                    self._runtime_cxn().ssh_config,
                    {
                        'connecttimeout': '15',
                        'forwardagent': 'yes',
                        'hostname': 'runtime',
                        'port': '666',
                        'proxycommand': 'my gateway',
                        'user': 'abaddon',
                    },
                )

            class hostname:
                def original_host_always_set(self):
                    cxn = Connection('somehost')
                    eq_(cxn.original_host, 'somehost')
                    eq_(cxn.host, 'somehost')

                def hostname_directive_overrides_host_attr(self):
                    # TODO: not 100% convinced this is the absolute most
                    # obvious API for 'translation' of given hostname to
                    # ssh-configured hostname, but it feels okay for now.
                    path = join(
                        support_path, 'ssh_config', 'overridden_hostname.conf'
                    )
                    config = Config(runtime_ssh_path=path)
                    cxn = Connection('aliasname', config=config)
                    eq_(cxn.host, 'realname')
                    eq_(cxn.original_host, 'aliasname')
                    eq_(cxn.port, 2222)

            class user:
                def wins_over_default(self):
                    eq_(self._runtime_cxn().user, 'abaddon')

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(overrides={'user': 'baal'})
                    eq_(cxn.user, 'abaddon')

                def loses_to_explicit(self):
                    # Would be 'abaddon', as above
                    config = self._runtime_config()
                    cxn = Connection('runtime', config=config, user='set')
                    eq_(cxn.user, 'set')

            class port:
                def wins_over_default(self):
                    eq_(self._runtime_cxn().port, 666)

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(overrides={'port': 777})
                    eq_(cxn.port, 666)

                def loses_to_explicit(self):
                    config = self._runtime_config() # Would be 666, as above
                    cxn = Connection('runtime', config=config, port=777)
                    eq_(cxn.port, 777)

            class forward_agent:
                def wins_over_default(self):
                    eq_(self._runtime_cxn().forward_agent, True)

                def wins_over_configuration(self):
                    # Of course, this "config override" is also the same as the
                    # default. Meh.
                    cxn = self._runtime_cxn(overrides={'forward_agent': False})
                    eq_(cxn.forward_agent, True)

                def loses_to_explicit(self):
                    # Would be True, as above
                    config = self._runtime_config()
                    cxn = Connection(
                        'runtime', config=config, forward_agent=False,
                    )
                    eq_(cxn.forward_agent, False)

            class proxy_command:
                def wins_over_default(self):
                    eq_(self._runtime_cxn().gateway, "my gateway")

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(overrides={'gateway': "meh gw"})
                    eq_(cxn.gateway, "my gateway")

                def loses_to_explicit(self):
                    # Would be "my gateway", as above
                    config = self._runtime_config()
                    cxn = Connection(
                        'runtime', config=config, gateway="other gateway",
                    )
                    eq_(cxn.gateway, "other gateway")

                def explicit_False_turns_off_feature(self):
                    # This isn't as necessary for things like user/port, which
                    # _may not_ be None in the end - this setting could be.
                    config = self._runtime_config()
                    cxn = Connection(
                        'runtime', config=config, gateway=False,
                    )
                    eq_(cxn.gateway, False)

            class proxy_jump:
                def setup(self):
                    self._expected_gw = Connection('jumpuser@jumphost:373')

                def wins_over_default(self):
                    cxn = self._runtime_cxn(basename='proxyjump')
                    eq_(cxn.gateway, self._expected_gw)

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(
                        basename='proxyjump',
                        overrides={'gateway': "meh gw"},
                    )
                    eq_(cxn.gateway, self._expected_gw)

                def loses_to_explicit(self):
                    # Would be a Connection equal to self._expected_gw, as
                    # above
                    config = self._runtime_config(basename='proxyjump')
                    cxn = Connection(
                        'runtime', config=config, gateway="other gateway",
                    )
                    eq_(cxn.gateway, "other gateway")

                def explicit_False_turns_off_feature(self):
                    config = self._runtime_config(basename='proxyjump')
                    cxn = Connection(
                        'runtime', config=config, gateway=False,
                    )
                    eq_(cxn.gateway, False)

                def wins_over_proxycommand(self):
                    cxn = self._runtime_cxn(basename='both_proxies')
                    eq_(cxn.gateway, Connection('winner@everything:777'))

                def multi_hop_works_ok(self):
                    cxn = self._runtime_cxn(basename='proxyjump_multi')
                    eq_(
                        cxn.gateway.gateway.gateway,
                        Connection('jumpuser3@jumphost3:411')
                    )
                    eq_(
                        cxn.gateway.gateway,
                        Connection('jumpuser2@jumphost2:872')
                    )
                    eq_(
                        cxn.gateway,
                        Connection('jumpuser@jumphost:373')
                    )

            class connect_timeout:
                def wins_over_default(self):
                    eq_(self._runtime_cxn().connect_timeout, 15)

                def wins_over_configuration(self):
                    cxn = self._runtime_cxn(
                        overrides={'timeouts': {'connect': 17}},
                    )
                    eq_(cxn.connect_timeout, 15)

                def loses_to_explicit(self):
                    config = self._runtime_config()
                    cxn = Connection(
                        'runtime', config=config, connect_timeout=23,
                    )
                    eq_(cxn.connect_timeout, 23)

            # TODO:
            # - IdentityFile
            # - What else can we quickly support as-is?

        class connect_kwargs:
            def defaults_to_empty_dict(self):
                eq_(Connection('host').connect_kwargs, {})

            def may_be_given_explicitly(self):
                cxn = Connection('host', connect_kwargs={'foo': 'bar'})
                eq_(cxn.connect_kwargs, {'foo': 'bar'})

            def may_be_configured(self):
                c = Config(overrides={'connect_kwargs': {'origin': 'config'}})
                cxn = Connection('host', config=c)
                eq_(cxn.connect_kwargs, {'origin': 'config'})

            def kwarg_wins_over_config(self):
                c = Config(overrides={'connect_kwargs': {'origin': 'config'}})
                cxn = Connection(
                    'host',
                    connect_kwargs={'origin': 'kwarg'},
                    config=c,
                )
                eq_(cxn.connect_kwargs, {'origin': 'kwarg'})

    class string_representation:
        "string representations"
        def str_displays_repr(self):
            c = Connection('meh')
            eq_(str(c), "<Connection host=meh>")

        def displays_core_params(self):
            c = Connection(user='me', host='there', port=123)
            template = "<Connection host=there user=me port=123>"
            eq_(repr(c), template)

        def omits_default_param_values(self):
            c = Connection('justhost')
            eq_(repr(c), "<Connection host=justhost>")

        def param_comparison_uses_config(self):
            conf = Config(overrides={'user': 'zerocool'})
            c = Connection(
                user='zerocool', host='myhost', port=123, config=conf
            )
            template = "<Connection host=myhost port=123>"
            eq_(repr(c), template)

        def proxyjump_gateway_shows_type(self):
            c = Connection(host='myhost', gateway=Connection('jump'))
            template = "<Connection host=myhost gw=proxyjump>"
            eq_(repr(c), template)

        def proxycommand_gateway_shows_type(self):
            c = Connection(host='myhost', gateway='netcat is cool')
            template = "<Connection host=myhost gw=proxycommand>"
            eq_(repr(c), template)

    class comparison_and_hashing:
        def comparison_uses_host_user_and_port(self):
            eq_(Connection('host'), Connection('host'))
            eq_(Connection('host', user='foo'), Connection('host', user='foo'))
            eq_(
                Connection('host', user='foo', port=123),
                Connection('host', user='foo', port=123),
            )

        def comparison_to_non_Connections_is_False(self):
            eq_(Connection('host') == 15, False)

        def hashing_works(self):
            eq_(hash(Connection('host')), hash(Connection('host')))

    class open:
        @patch('fabric.connection.SSHClient')
        def has_no_required_args_and_returns_None(self, Client):
            eq_(Connection('host').open(), None)

        @patch('fabric.connection.SSHClient')
        def calls_SSHClient_connect(self, Client):
            "calls paramiko.SSHClient.connect() with correct args"
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            Connection('host').open()
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname='host',
                port=22,
            )

        @patch('fabric.connection.SSHClient')
        def passes_through_connect_kwargs(self, Client):
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            Connection('host', connect_kwargs={'foobar': 'bizbaz'}).open()
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname='host',
                port=22,
                foobar='bizbaz',
            )

        @patch('fabric.connection.SSHClient')
        def refuses_to_overwrite_connect_kwargs_with_others(self, Client):
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            for key, value, kwargs in (
                # Core connection args should definitely not get overwritten!
                # NOTE: recall that these keys are the SSHClient.connect()
                # kwarg names, NOT our own config/kwarg names!
                ('hostname', 'nothost', {}),
                ('port', 17, {}),
                ('username', 'zerocool', {}),
                # These might arguably still be allowed to work, but let's head
                # off confusion anyways.
                ('timeout', 100, {'connect_timeout': 25}),
            ):
                try:
                    Connection(
                        'host',
                        connect_kwargs={key: value},
                        **kwargs
                    ).open()
                except ValueError as e:
                    err = "Refusing to be ambiguous: connect() kwarg '{0}' was given both via regular arg and via connect_kwargs!" # noqa
                    eq_(str(e), err.format(key))
                else:
                    assert False, "Did not raise ValueError!"

        @patch('fabric.connection.SSHClient')
        def connect_kwargs_protection_not_tripped_by_defaults(self, Client):
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            Connection('host', connect_kwargs={'timeout': 300}).open()
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname='host',
                port=22,
                timeout=300,
            )

        @patch('fabric.connection.SSHClient')
        def submits_connect_timeout(self, Client):
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            Connection('host', connect_timeout=27).open()
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname='host',
                port=22,
                timeout=27,
            )

        @patch('fabric.connection.SSHClient')
        def is_connected_True_when_successful(self, Client):
            # Ensure the parts of Paramiko we test act like things are cool
            client = Client.return_value
            client.get_transport.return_value = Mock(active=True)
            c = Connection('host')
            c.open()
            eq_(c.is_connected, True)

        @patch('fabric.connection.SSHClient')
        def has_no_effect_if_already_connected(self, Client):
            cxn = Connection('host')
            client = Client.return_value
            # First open() never gets to .active; subsequently it needs to
            # appear connected, so True.
            client.get_transport.return_value.active = True
            cxn.open()
            cxn.open()
            eq_(client.connect.call_count, 1)

        @patch('fabric.connection.SSHClient')
        def is_connected_still_False_when_connect_fails(self, Client):
            cxn = Connection('host')
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            client.connect.side_effect = socket.error
            try:
                cxn.open()
            except socket.error:
                pass
            eq_(cxn.is_connected, False)

        @patch('fabric.connection.SSHClient')
        def uses_configured_user_host_and_port(self, Client):
            cxn = Connection(user='myuser', host='myhost', port=9001)
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            cxn.open()
            client.connect.assert_called_once_with(
                username='myuser',
                hostname='myhost',
                port=9001,
            )

        @patch('fabric.connection.SSHClient')
        def uses_gateway_channel_as_sock_for_SSHClient_connect(self, Client):
            "uses Connection gateway as 'sock' arg to SSHClient.connect"
            # Setup
            mock_gw = Mock()
            mock_main = Mock()
            Client.side_effect = [mock_gw, mock_main]
            gw = Connection('otherhost')
            gw.open = Mock(wraps=gw.open)
            main = Connection('host', gateway=gw)
            main.open()
            # Expect gateway is also open()'d
            gw.open.assert_called_once_with()
            # Expect direct-tcpip channel open on 1st client
            open_channel = mock_gw.get_transport.return_value.open_channel
            kwargs = open_channel.call_args[1]
            eq_(kwargs['kind'], 'direct-tcpip')
            eq_(kwargs['dest_addr'], ('host', 22))
            # Expect result of that channel open as sock arg to connect()
            sock_arg = mock_main.connect.call_args[1]['sock']
            ok_(sock_arg is open_channel.return_value)

        @patch('fabric.connection.SSHClient')
        @patch('fabric.connection.ProxyCommand')
        def uses_proxycommand_as_sock_for_Client_connect(self, moxy, Client):
            "uses ProxyCommand from gateway as 'sock' arg to SSHClient.connect"
            # Setup
            cxn = Mock()
            Client.return_value = cxn
            main = Connection('host', gateway="net catty %h %p")
            main.open()
            # Expect ProxyCommand instantiation
            moxy.assert_called_once_with("net catty host 22")
            # Expect result of that as sock arg to connect()
            sock_arg = cxn.connect.call_args[1]['sock']
            ok_(sock_arg is moxy.return_value)

        # TODO: all the various connect-time options such as agent forwarding,
        # host acceptance policies, how to auth, etc etc. These are all aspects
        # of a given session and not necessarily the same for entire lifetime
        # of a Connection object, should it ever disconnect/reconnect.
        # TODO: though some/all of those things might want to be set to
        # defaults at initialization time...

    class close:
        @patch('fabric.connection.SSHClient')
        def has_no_required_args_and_returns_None(self, Client):
            c = Connection('host')
            c.open()
            eq_(c.close(), None)

        @patch('fabric.connection.SSHClient')
        def calls_SSHClient_close(self, Client):
            "calls paramiko.SSHClient.close()"
            c = Connection('host')
            c.open()
            c.close()
            client = Client.return_value
            client.close.assert_called_with()

        @patch('fabric.connection.SSHClient')
        @patch('fabric.connection.AgentRequestHandler')
        def calls_agent_handler_close_if_enabled(self, Handler, Client):
            c = Connection('host', forward_agent=True)
            c.create_session()
            c.close()
            # NOTE: this will need to change if, for w/e reason, we ever want
            # to run multiple handlers at once
            Handler.return_value.close.assert_called_once_with()

        @patch('fabric.connection.SSHClient')
        def has_no_effect_if_already_closed(self, Client):
            client = Client.return_value
            c = Connection('host')
            # Expected flow:
            # - Connection.open() asks is_connected which checks
            # self.transport, which is initially None, so .active isn't even
            # checked.
            # - First Connection.close() asks is_connected and that needs to be
            # True, so we want .active to retuen True.
            # - Second Connection.close() also asks is_connected which needs to
            # False this time.
            prop = PropertyMock(side_effect=[True, False])
            type(client.get_transport.return_value).active = prop
            c.open()
            c.close()
            c.close()
            client.close.assert_called_once_with()

        @patch('fabric.connection.SSHClient')
        def is_connected_becomes_False(self, Client):
            client = Client.return_value
            client.get_transport.return_value = None
            c = Connection('host')
            c.open()
            c.close()
            eq_(c.is_connected, False)

        @patch('fabric.connection.SSHClient')
        def class_works_as_a_closing_contextmanager(self, Client):
            client = Client.return_value
            with Connection('host') as c:
                c.open()
            client.close.assert_called_once_with()

    class create_session:
        @patch('fabric.connection.SSHClient')
        def calls_open_for_you(self, Client):
            c = Connection('host')
            c.open = Mock()
            c.transport = Mock() # so create_session no asplode
            c.create_session()
            ok_(c.open.called)

        @patch('fabric.connection.SSHClient')
        @patch('fabric.connection.AgentRequestHandler')
        def activates_paramiko_agent_forwarding_if_configured(
            self, Handler, Client
        ):
            c = Connection('host', forward_agent=True)
            chan = c.create_session()
            Handler.assert_called_once_with(chan)

    class run:
        # NOTE: most actual run related tests live in the runners module's
        # tests. Here we are just testing the outer interface a bit.

        @patch('fabric.connection.SSHClient')
        @patch(remote_path)
        def calls_open_for_you(self, Remote, Client):
            c = Connection('host')
            c.open = Mock()
            c.run("command")
            ok_(c.open.called)

        @patch('fabric.connection.SSHClient')
        @patch(remote_path)
        def calls_Remote_run_with_command_and_kwargs_and_returns_its_result(
            self, Remote, Client
        ):
            remote = Remote.return_value
            sentinel = object()
            remote.run.return_value = sentinel
            c = Connection('host')
            r1 = c.run("command")
            r2 = c.run("command", warn=True, hide='stderr')
            # NOTE: somehow, .call_args & the methods built on it (like
            # .assert_called_with()) stopped working, apparently triggered by
            # our code...somehow...after commit (roughly) 80906c7.
            # And yet, .call_args_list and its brethren work fine. Wha?
            Remote.assert_any_call(c)
            remote.run.assert_has_calls([
                call("command"),
                call("command", warn=True, hide='stderr'),
            ])
            for r in (r1, r2):
                ok_(r is sentinel)

    class local:
        # NOTE: most tests for this functionality live in Invoke's runner
        # tests.
        @patch('invoke.config.Local')
        def calls_invoke_Local_run(self, Local):
            Connection('host').local('foo')
            # NOTE: yet another casualty of the bizarre mock issues
            ok_(call().run('foo') in Local.mock_calls)

    class sudo:
        @patch('fabric.connection.SSHClient')
        @patch(remote_path)
        def calls_open_for_you(self, Remote, Client):
            c = Connection('host')
            c.open = Mock()
            c.sudo("command")
            ok_(c.open.called)

        @patch('fabric.connection.SSHClient')
        @patch(remote_path)
        def basic_invocation(self, Remote, Client):
            # Technically duplicates Invoke-level tests, but ensures things
            # still work correctly at our level.
            cxn = Connection('host')
            cxn.sudo('foo')
            cmd = "sudo -S -p '{0}' foo".format(cxn.config.sudo.prompt)
            # NOTE: this is another spot where Mock.call_args is inexplicably
            # None despite call_args_list being populated. WTF. (Also,
            # Remote.return_value is two different Mocks now, despite Remote's
            # own Mock having the same ID here and in code under test. WTF!!)
            eq_(
                Remote.mock_calls,
                [call(cxn), call().run(cmd, watchers=ANY)]
            )
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
        @patch('fabric.connection.SSHClient')
        def returns_result_of_client_open_sftp(self, SSHClient):
            "returns result of client.open_sftp()"
            client = SSHClient.return_value
            sentinel = object()
            client.open_sftp.return_value = sentinel
            eq_(Connection('host').sftp(), sentinel)
            client.open_sftp.assert_called_with()

        @patch('fabric.connection.SSHClient')
        def lazily_caches_result(self, SSHClient):
            client = SSHClient.return_value
            sentinel1, sentinel2 = object(), object()
            client.open_sftp.side_effect = [sentinel1, sentinel2]
            cxn = Connection('host')
            first = cxn.sftp()
            # TODO: why aren't we just asserting about calls of open_sftp???
            err = "{0!r} wasn't the sentinel object()!"
            ok_(first is sentinel1, err.format(first))
            second = cxn.sftp()
            ok_(second is sentinel1, err.format(second))

    class get:
        @patch('fabric.connection.Transfer')
        def calls_Transfer_get(self, Transfer):
            "calls Transfer.get()"
            c = Connection('host')
            c.get('meh')
            Transfer.assert_called_with(c)
            Transfer.return_value.get.assert_called_with('meh')

    class put:
        @patch('fabric.connection.Transfer')
        def calls_Transfer_put(self, Transfer):
            "calls Transfer.put()"
            c = Connection('host')
            c.put('meh')
            Transfer.assert_called_with(c)
            Transfer.return_value.put.assert_called_with('meh')

    class forward_local:
        @patch('fabric.tunnels.select')
        @patch('fabric.tunnels.socket.socket')
        @patch('fabric.connection.SSHClient')
        def _forward_local(self, kwargs, Client, mocket, select):
            # Tease out bits of kwargs for use in the mocking/expecting.
            # But leave it alone for raw passthru to the API call itself.
            # TODO: unhappy with how much this apes the real code & its sig...
            local_port = kwargs['local_port']
            remote_port = kwargs.get('remote_port', local_port)
            local_host = kwargs.get('local_host', 'localhost')
            remote_host = kwargs.get('remote_host', 'localhost')
            # These aren't part of the real sig, but this is easier than trying
            # to reconcile the mock decorators + optional-value kwargs. meh.
            tunnel_exception = kwargs.pop('tunnel_exception', None)
            listener_exception = kwargs.pop('listener_exception', False)
            # Mock setup
            client = Client.return_value
            listener_sock = Mock(name='listener_sock')
            if listener_exception:
                listener_sock.bind.side_effect = listener_exception
            data = b("Some data")
            tunnel_sock = Mock(name='tunnel_sock', recv=lambda n: data)
            local_addr = Mock()
            transport = client.get_transport.return_value
            channel = transport.open_channel.return_value
            # socket.socket is only called once directly
            mocket.return_value = listener_sock
            # The 2nd socket is obtained via an accept() (which should only
            # fire once & raise EAGAIN after)
            listener_sock.accept.side_effect = chain(
                [(tunnel_sock, local_addr)],
                repeat(socket.error(errno.EAGAIN, "nothing yet")),
            )
            obj = tunnel_sock if tunnel_exception is None else tunnel_exception
            select.select.side_effect = _select_result(obj)
            with Connection('host').forward_local(**kwargs):
                # Make sure we give listener thread enough time to boot up :(
                # Otherwise we might assert before it does things. (NOTE:
                # doesn't need to be much, even at 0.01s, 0/100 trials failed
                # (vs 45/100 with no sleep)
                time.sleep(0.015)
                eq_(client.connect.call_args[1]['hostname'], 'host')
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
                        'direct-tcpip',
                        (remote_host, remote_port),
                        local_addr,
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
            self._forward_local({'local_port': 1234})

        def distinct_remote_port(self):
            self._forward_local({
                'local_port': 1234,
                'remote_port': 4321,
            })

        def non_localhost_listener(self):
            self._forward_local({
                'local_port': 1234,
                'local_host': 'nearby_local_host',
            })

        def non_remote_localhost_connection(self):
            self._forward_local({
                'local_port': 1234,
                'remote_host': 'nearby_remote_host',
            })

        def _thread_error(self, which):
            class Sentinel(Exception):
                pass
            try:
                self._forward_local({
                    'local_port': 1234,
                    '{0}_exception'.format(which): Sentinel,
                })
            except ThreadException as e:
                # NOTE: ensures that we're getting what we expected and not
                # some deeper, test-bug related error
                eq_(len(e.exceptions), 1)
                inner = e.exceptions[0]
                err = "Expected wrapped exception to be Sentinel, was {0}"
                ok_(inner.type is Sentinel, err.format(inner.type.__name__))
            else:
                # no exception happened :( implies the thread went boom but
                # nobody noticed
                err = "Failed to get ThreadException on {0} error"
                assert False, err.format(which)

        def tunnel_errors_bubble_up(self):
            self._thread_error('tunnel')

        def tunnel_manager_errors_bubble_up(self):
            self._thread_error('listener')

        # TODO: these require additional refactoring of _forward_local to be
        # more like the decorators in _util
        def multiple_tunnels_can_be_open_at_once(self):
            skip()

    class forward_remote:
        @patch('fabric.connection.socket.socket')
        @patch('fabric.tunnels.select')
        @patch('fabric.connection.SSHClient')
        def _forward_remote(self, kwargs, Client, select, mocket):
            # TODO: unhappy with how much this duplicates of the code under
            # test, re: sig/default vals
            # Set up parameter values/defaults
            remote_port = kwargs['remote_port']
            remote_host = kwargs.get('remote_host', '127.0.0.1')
            local_port = kwargs.get('local_port', remote_port)
            local_host = kwargs.get('local_host', 'localhost')
            # Mock/etc setup, anything that can be prepped before the forward
            # occurs (which is most things)
            tun_socket = mocket.return_value
            cxn = Connection('host')
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
                eq_(call[1]['address'], remote_host)
                eq_(call[1]['port'], remote_port)
                # Pretend the Transport called our callback with mock Channel
                call[1]['handler'](chan, tuple(), tuple())
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
            eq_(cxn.transport.cancel_port_forward.call_count, 1)

        def forwards_remote_port_to_local_end(self):
            self._forward_remote({'remote_port': 1234})

        def distinct_local_port(self):
            self._forward_remote({
                'remote_port': 1234,
                'local_port': 4321,
            })

        def non_localhost_connections(self):
            self._forward_remote({
                'remote_port': 1234,
                'local_host': 'nearby_local_host',
            })

        def remote_non_localhost_listener(self):
            self._forward_remote({
                'remote_port': 1234,
                'remote_host': '192.168.1.254',
            })

        # TODO: these require additional refactoring of _forward_remote to be
        # more like the decorators in _util
        def multiple_tunnels_can_be_open_at_once(self):
            skip()

        def tunnel_errors_bubble_up(self):
            skip()

        def listener_errors_bubble_up(self):
            skip()
