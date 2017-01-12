from itertools import chain, repeat
from invoke.vendor.six import b
import errno
import socket
import time

from spec import Spec, eq_, raises, ok_, skip
from mock import patch, Mock, call, PropertyMock
from paramiko.client import SSHClient, AutoAddPolicy

from invoke.exceptions import ThreadException

from fabric.connection import Connection, Config, Group
from fabric.util import get_local_user


class Connection_(Spec):
    class basic_attributes:
        def is_connected_defaults_to_False(self):
            eq_(Connection('host').is_connected, False)

        def client_defaults_to_a_new_SSHClient(self):
            c = Connection('host').client
            ok_(isinstance(c, SSHClient))
            eq_(c.get_transport(), None)

        def host_string(self):
            eq_(
                Connection('host').host_string,
                '{0}@host:22'.format(get_local_user())
            )
            eq_(
                Connection('host', user='user').host_string,
                'user@host:22'
            )
            eq_(
                Connection('host', user='user', port=1234).host_string,
                'user@host:1234'
            )

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
                config = Config(overrides={'forward_agent': True})
                eq_(Connection('host', config=config).forward_agent, True)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', forward_agent=True).forward_agent, True)

            def kwarg_wins_over_config(self):
                config = Config(overrides={'forward_agent': True})
                cxn = Connection('host', forward_agent=False, config=config)
                eq_(cxn.forward_agent, False)

        class key_filename:
            def defaults_to_None(self):
                eq_(Connection('host').key_filename, None)

            def exposed_as_attribute(self):
                c = Connection('host', key_filename='foo.key')
                eq_(c.key_filename, 'foo.key')

        class config:
            def is_not_required(self):
                eq_(Connection('host').config.__class__, Config)

            def can_be_specified(self):
                c = Config(overrides={'user': 'me', 'custom': 'option'})
                config = Connection('host', config=c).config
                ok_(c is config)
                eq_(config['user'], 'me')
                eq_(config['custom'], 'option')

            def inserts_missing_default_keys(self):
                c = Connection('host', config=Config())
                eq_(c.config['port'], 22)
                eq_(c.config['forward_agent'], False)

            def defaults_to_merger_of_global_defaults(self):
                # I.e. our global_defaults + Invoke's global_defaults
                c = Connection('host')
                # From invoke's global_defaults
                eq_(c.config.run.warn, False)
                # From ours
                eq_(c.config.port, 22)

            def our_config_has_various_default_keys(self):
                # NOTE: Duplicates some other tests but we're now starting to
                # grow options not directly related to user/port stuff, so best
                # to have at least one test listing all expected keys.
                c = Connection('host')
                for keyparts in (
                    ('port',),
                    ('user',),
                    ('forward_agent',),
                    ('sudo', 'prompt'),
                    ('sudo', 'password'),
                ):
                    obj = c.config
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
                    eq_(Connection('host').config.run.warn, "nope lol")

            def we_override_replace_env(self):
                eq_(Connection('host').config.run.replace_env, True)

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

    class string_representation:
        "string representations"
        def str_displays_repr(self):
            c = Connection('meh')
            eq_(str(c), "<Connection id={0} host='meh'>".format(id(c)))

        def displays_core_params(self):
            c = Connection(user='me', host='there', port=123)
            template = "<Connection id={0} user='me' host='there' port=123>"
            eq_(repr(c), template.format(id(c)))

        def omits_default_param_values(self):
            c = Connection('justhost')
            eq_(repr(c), "<Connection id={0} host='justhost'>".format(id(c)))

        def param_comparison_uses_config(self):
            conf = Config(overrides={'user': 'zerocool'})
            c = Connection(
                user='zerocool', host='myhost', port=123, config=conf
            )
            template = "<Connection id={0} host='myhost' port=123>"
            eq_(repr(c), template.format(id(c)))

        def direct_tcpip_gateway_shows_type(self):
            c = Connection(host='myhost', gateway=Connection('jump'))
            template = "<Connection id={0} host='myhost' gw=direct-tcpip>"
            eq_(repr(c), template.format(id(c)))

        def proxycommand_gateway_shows_type(self):
            c = Connection(host='myhost', gateway='netcat is cool')
            template = "<Connection id={0} host='myhost' gw=proxy>"
            eq_(repr(c), template.format(id(c)))

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
        def passes_through_kwargs(self, Client):
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            Connection('host').open(foobar='bizbaz')
            client.connect.assert_called_with(
                username=get_local_user(),
                hostname='host',
                port=22,
                foobar='bizbaz',
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
        def uses_configured_key_filename(self, Client):
            cxn = Connection(host='myhost', key_filename='foo.key')
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            cxn.open()
            client.connect.assert_called_once_with(
                username=get_local_user(),
                hostname='myhost',
                key_filename='foo.key',
                port=22,
            )

        @patch('fabric.connection.SSHClient')
        def key_filename_can_be_list_too(self, Client):
            names = ['foo.key', 'bar.key']
            cxn = Connection(host='myhost', key_filename=names)
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            cxn.open()
            client.connect.assert_called_once_with(
                username=get_local_user(),
                hostname='myhost',
                key_filename=names,
                port=22,
            )

        @patch('fabric.connection.SSHClient')
        def uses_configured_key_as_pkey(self, Client):
            dummy = Mock('key') # No need to deal with a 'real' PKey subclass
            cxn = Connection(host='myhost', key=dummy)
            client = Client.return_value
            client.get_transport.return_value = Mock(active=False)
            cxn.open()
            client.connect.assert_called_once_with(
                username=get_local_user(),
                hostname='myhost',
                pkey=dummy,
                port=22,
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
            chan = c.create_session()
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
            _ = c.create_session()
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
        @patch('fabric.connection.Remote')
        def calls_open_for_you(self, Remote, Client):
            c = Connection('host')
            c.open = Mock()
            c.run("command")
            ok_(c.open.called)

        @patch('fabric.connection.SSHClient')
        @patch('fabric.connection.Remote')
        def calls_Remote_run_with_command_and_kwargs_and_returns_its_result(
            self, Remote, Client
        ):
            remote = Remote.return_value
            sentinel = object()
            remote.run.return_value = sentinel
            c = Connection('host')
            r1 = c.run("command")
            r2 = c.run("command", warn=True, hide='stderr')
            Remote.assert_called_with(context=c)
            remote.run.assert_has_calls([
                call("command"),
                call("command", warn=True, hide='stderr'),
            ])
            for r in (r1, r2):
                ok_(r is sentinel)

    class local:
        # NOTE: most tests for this functionality live in Invoke's runner
        # tests.
        @patch('invoke.context.Local')
        def calls_invoke_Local_run(self, Local):
            Connection('host').local('foo')
            Local.return_value.run.assert_called_with('foo')

    class sudo:
        @patch('fabric.connection.SSHClient')
        @patch('fabric.connection.Remote')
        @patch('invoke.context.getpass')
        def basic_invocation(self, getpass, Remote, Client):
            # Technically duplicates Invoke-level tests, but ensures things
            # still work correctly at our level.
            cxn = Connection('host')
            expected = Remote.return_value.run.return_value
            result = cxn.sudo('foo')
            cmd = "sudo -S -p '{0}' foo".format(cxn.config.sudo.prompt)
            eq_(Remote.return_value.run.call_args[0][0], cmd)
            ok_(result is expected, "sudo() did not return run()'s result!!")

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
            ok_(cxn.sftp() is sentinel1)
            ok_(cxn.sftp() is sentinel1)

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
            tunnel_exception = kwargs.pop('tunnel_exception', False)
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
            # select.select() returns three N-tuples. Have it just act like a
            # single read event happened, then quiet after. So chain a
            # single-item iterable to a repeat(). (Mock has no built-in way to
            # do this apparently.)
            initial = [(tunnel_sock,), tuple(), tuple()]
            if tunnel_exception:
                initial = tunnel_exception
            select.select.side_effect = chain(
                [initial],
                repeat([tuple(), tuple(), tuple()]),
            )
            with Connection('host').forward_local(**kwargs):
                # Make sure we give listener thread enough time to boot up :(
                # Otherwise we might assert before it does things. (NOTE:
                # doesn't need to be much, even at 0.01s, 0/100 trials failed
                # (vs 45/100 with no sleep)
                time.sleep(0.01)
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
            time.sleep(0.01)
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
                    '{}_exception'.format(which): Sentinel,
                })
            except ThreadException as e:
                # NOTE: ensures that we're getting what we expected and not
                # some deeper, test-bug related error
                eq_(len(e.exceptions), 1)
                inner = e.exceptions[0]
                err = "Expected wrapped exception to be Sentinel, was {}".format(inner.type.__name__)
                ok_(inner.type is Sentinel, err)
            else:
                # no exception happened :( implies the thread went boom but
                # nobody noticed
                err = "Failed to get ThreadException on {} error".format(which)
                assert False, err

        def tunnel_errors_bubble_up(self):
            self._thread_error('tunnel')

        def tunnel_manager_errors_bubble_up(self):
            self._thread_error('listener')

        # TODO: these require additional refactoring of _forward_local to be
        # more like the decorators in _util
        def multiple_tunnels_can_be_open_at_once(self):
            skip()

    class forward_remote:
        @patch('fabric.connection.SSHClient')
        def _forward_remote(self, kwargs, Client):
            # TODO: implement this; it'll be semi similar to _forward_local
            # above, but distinct in that its main assertion is that
            # `sock.connect` is called to the local end, and its .write is
            # called with data submitted to a mock of whatever Paramiko is
            # doing inside request_port_forward.
            skip()

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

class Group_(Spec):
    class init:
        "__init__"
        def may_be_empty(self):
            eq_(len(Group()), 0)

        def takes_iterable_of_host_strings(self):
            g = Group(('foo', 'bar'))
            eq_(g[0].host, 'foo')
            eq_(g[1].host, 'bar')

    class from_connections:
        def inits_from_iterable_of_Connections(self):
            g = Group.from_connections((Connection('foo'), Connection('bar')))
            eq_(len(g), 2)
            eq_(g[1].host, 'bar')

    def acts_like_an_iterable_of_Connections(self):
        g = Group(('foo', 'bar', 'biz'))
        eq_(g[0].host, 'foo')
        eq_(g[-1].host, 'biz')
        eq_(len(g), 3)
        for c in g:
            ok_(isinstance(c, Connection))

    class run:
        def executes_arguments_on_contents_run_serially(self):
            "executes arguments on contents' run() serially"
            cxns = [Connection('host1'), Connection('host2')]
            for cxn in cxns:
                cxn.run = Mock()
            g = Group.from_connections(cxns)
            g.run("command", hide=True, warn=True)
            for cxn in cxns:
                cxn.run.assert_called_with("command", hide=True, warn=True)

        def returns_map_of_normalized_host_string_to_result(self):
            c1 = Connection('host1', user='foo', port=222)
            c2 = Connection('host2')
            cxns = [c1, c2]
            for cxn in cxns:
                # Just have mocked run() return the object itself for easy
                # identification of which object a result came from.
                cxn.run = Mock(return_value=cxn)
            g = Group.from_connections(cxns)
            result = g.run("command", hide=True, warn=True)
            ok_(result['foo@host1:222'] is c1)
            # Proves normalization
            hs = '{0}@host2:22'.format(get_local_user())
            ok_(result[hs] is c2)
