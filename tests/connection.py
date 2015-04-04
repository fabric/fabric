import copy

from spec import Spec, skip, eq_, raises, assert_raises
from mock import patch, Mock

from invoke.config import Config
from invoke import config # For mocking/tweaking

from fabric.connection import Connection
from fabric.utils import get_local_user


class Connection_(Spec):
    class basic_attributes:
        def is_connected_defaults_to_False(self):
            skip()

    class init:
        "__init__"

        class host:
            @raises(TypeError)
            def is_required(self):
                Connection()

        class user:
            def defaults_to_local_user_with_no_config(self):
                # Tautology-tastic!
                eq_(Connection('host').user, get_local_user())

            def accepts_config_user_option(self):
                config = Config({'user': 'nobody', 'port': 22})
                eq_(Connection('host', config=config).user, 'nobody')

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', user='somebody').user, 'somebody')

        class port:
            def defaults_to_22_because_yup(self):
                eq_(Connection('host').port, 22)

            def defaults_to_configuration_port(self):
                config = Config({'port': 2222, 'user': 'lol'})
                eq_(Connection('host', config=config).port, 2222)

            def may_be_given_as_kwarg(self):
                eq_(Connection('host', port=2202).port, 2202)

        class config:
            def is_not_required(self):
                eq_(Connection('host').config.__class__, Config)

            def can_be_specified(self):
                c = Config({'user': 'me', 'port': 22, 'run': {}, 'tasks': {}})
                eq_(Connection('host', config=c).config, c)

            def gets_mad_if_missing_keys(self):
                skip()

            def defaults_to_merger_of_global_defaults(self):
                c = Connection('host')
                # From invoke's global_defaults
                eq_(c.config.run.warn, False)
                # From ours
                eq_(c.config.port, 22)

            def our_defaults_override_invokes(self):
                "our defaults override invoke's"
                backup = copy.deepcopy(config.global_defaults)
                try:
                    # Override an invoke setting
                    config.global_defaults['run']['warn'] = "nope lol"
                    eq_(Connection('host').config.run.warn, "nope lol")
                finally:
                    config.global_defaults = backup

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
