import socket

from spec import Spec, eq_, raises, ok_
from mock import patch, Mock, call
from paramiko.client import SSHClient, AutoAddPolicy

from fabric.connection import Connection, Config, Group
from fabric.utils import get_local_user


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

            def defaults_to_merger_of_global_defaults(self):
                c = Connection('host')
                # From invoke's global_defaults
                eq_(c.config.run.warn, False)
                # From ours
                eq_(c.config.port, 22)

            def our_defaults_override_invokes(self):
                "our defaults override invoke's"
                with patch.object(
                    Config,
                    'global_defaults',
                    return_value={
                        'run': {'warn': "nope lol"},
                        'user': 'me',
                        'port': 22,
                    }
                ):
                    # If our global_defaults didn't win, this would still
                    # resolve to False.
                    eq_(Connection('host').config.run.warn, "nope lol")

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
                hostname='host',
                port=22,
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
            client.get_transport.return_value = Mock(active=False)
            cxn.open()
            client.get_transport.return_value = Mock(active=True)
            cxn.open()
            client.connect.assert_called_once_with(
                hostname='host',
                port=22,
            )

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
        def calls_SSHClient_connect(self, Client):
            "calls paramiko.SSHClient.close()"
            c = Connection('host')
            c.open()
            c.close()
            client = Client.return_value
            client.close.assert_called_with()

        @patch('fabric.connection.SSHClient')
        def has_no_effect_if_already_closed(self, Client):
            client = Client.return_value
            c = Connection('host')
            c.open()
            c.close()
            client.get_transport.return_value = Mock(active=False)
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
        @patch('fabric.connection.invoke')
        def calls_invoke_Runner_run(self, invoke):
            Connection('host').local('foo')
            invoke.run.assert_called_with('foo')

    class sftp:
        @patch('fabric.connection.SSHClient')
        def returns_result_of_client_open_sftp(self, SSHClient):
            "returns result of client.open_sftp()"
            client = SSHClient.return_value
            sentinel = object()
            client.open_sftp.return_value = sentinel
            eq_(Connection('host').sftp(), sentinel)
            client.open_sftp.assert_called_with()

    class get:
        @patch('fabric.connection.Transfer')
        def calls_Transfer_get(self, Transfer):
            "calls Transfer.get()"
            c = Connection('host')
            c.get('meh')
            Transfer.assert_called_with(c)
            Transfer.return_value.get.assert_called_with('meh')


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
