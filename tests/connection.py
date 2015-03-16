from spec import Spec, skip, eq_, raises
from mock import patch, Mock

from invoke.config import Config

from fabric import Connection
from fabric.utils import get_local_user


class Connection_(Spec):
    class init:
        "__init__"

        @raises(TypeError)
        def host_required(self):
            Connection()

        class user:
            def defaults_to_system_user_with_no_config(self):
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
