from spec import Spec, skip, eq_, raises
from mock import patch, Mock

from invoke.config import Config

from fabric import Connection
from fabric.utils import get_local_user


class Connection_(Spec):
    class basic_attributes:
        def is_connected_defaults_to_False(self):
            skip()

    class init:
        "__init__"

        @raises(TypeError)
        def host_required(self):
            Connection()

        class user:
            def defaults_to_local_user_with_no_config(self):
                # Tautology-tastic!
                eq_(Connection('host').user, get_local_user())

            def accepts_config_user_option(self):
                config = Config({'user': 'nobody'})
                eq_(Connection('host', config=config).user, 'nobody')

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', user='somebody').user, 'somebody')

        class port:
            def defaults_to_22_because_yup(self):
                eq_(Connection('host').port, 22)

            def defaults_to_configuration_port(self):
                config = Config({'port': 2222})
                eq_(Connection('host', config=config).port, 2222)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', port=2202).port, 2202)

    class open:
        def has_no_required_args_and_returns_None(self):
            # Connection(host).open()
            skip()

        def calls_Client_connect(self):
            "calls paramiko.Client.connect()"
            # Mock Client somehow
            skip()

        def sets_is_connected_flag_when_successful(self):
            # c = Connection(host)
            # c.open()
            # eq_(c.is_connected, True)
            skip()

        def is_connected_still_False_when_connect_fails(self):
            skip()

        def raises_some_sort_of_error_when_shit_explodes_idk(self):
            # ???
            skip()

        # TODO: all the various connect-time options such as agent forwarding,
        # host acceptance policies, how to auth, etc etc. These are all aspects
        # of a given session and not necessarily the same for entire lifetime
        # of a Connection object, should it ever disconnect/reconnect.
        # TODO: though some/all of those things might want to be set to
        # defaults at initialization time...

    class close:
        def calls_Client_close(self):
            "calls paramiko.Client.close()"
            skip()

        def sets_is_connected_to_False(self):
            skip()

        def sets_is_connected_to_False_even_on_error(self):
            skip()
