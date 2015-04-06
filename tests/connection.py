from spec import Spec, skip, eq_, raises, ok_
from mock import patch, Mock
from paramiko.client import SSHClient, AutoAddPolicy

from fabric.connection import Connection, Config
from fabric.utils import get_local_user


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
            ok_(isinstance(Connection('host').client._policy, AutoAddPolicy))

    class init:
        "__init__"

        class host:
            @raises(TypeError)
            def is_required(self):
                Connection()

            def is_exposed_as_attribute(self):
                eq_(Connection('host').host, 'host') # buffalo buffalo

        class user:
            def defaults_to_local_user_with_no_config(self):
                # Tautology-tastic!
                eq_(Connection('host').user, get_local_user())

            def accepts_config_user_option(self):
                config = Config(overrides={'user': 'nobody'})
                eq_(Connection('host', config=config).user, 'nobody')

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', user='somebody').user, 'somebody')

        class port:
            def defaults_to_22_because_yup(self):
                eq_(Connection('host').port, 22)

            def accepts_configuration_port(self):
                config = Config(overrides={'port': 2222})
                eq_(Connection('host', config=config).port, 2222)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', port=2202).port, 2202)

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
        def has_no_required_args_and_returns_None(self, client):
            eq_(Connection('host').open(), None)

        @patch('fabric.connection.SSHClient')
        def calls_SSHClient_connect(self, Client):
            "calls paramiko.SSHClient.connect() with correct args"
            Connection('host').open()
            client = Client.return_value
            client.connect.assert_called_with(
                hostname='host',
                port=22,
            )

        @patch('fabric.connection.SSHClient')
        def sets_is_connected_flag_when_successful(self, Client):
            # Ensure the parts of Paramiko we test act like things are cool
            client = Client.return_value
            client.get_transport.return_value = Mock(active=True)
            c = Connection('host')
            c.open()
            eq_(c.is_connected, True)

        def has_no_effect_if_already_connected(self):
            skip()

        def is_connected_still_False_when_connect_fails(self):
            skip()

        def raises_some_sort_of_error_when_shit_explodes_idk(self):
            # ???
            skip()

        def is_connected_is_False_even_if_failure_doesnt_raise_exception(self):
            # i.e. client.connect() didn't die BUT somehow its transport is
            # none, or its transport says it's inactive
            skip()

        # TODO: all the various connect-time options such as agent forwarding,
        # host acceptance policies, how to auth, etc etc. These are all aspects
        # of a given session and not necessarily the same for entire lifetime
        # of a Connection object, should it ever disconnect/reconnect.
        # TODO: though some/all of those things might want to be set to
        # defaults at initialization time...

        def honors_config_option_for_known_hosts(self):
            skip()

    class close:
        def calls_Client_close(self):
            "calls paramiko.Client.close()"
            skip()

        def sets_is_connected_to_False(self):
            skip()

        def sets_is_connected_to_False_even_on_error(self):
            skip()
