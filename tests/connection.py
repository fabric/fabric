from spec import Spec, skip, eq_, raises
from mock import patch, Mock

from fabric import Connection, Configuration


class Connection_(Spec):
    class init:
        "__init__"

        @raises(TypeError)
        def host_required(self):
            Connection()

        def user_defaults_to_configuration_local_user(self):
            config = Configuration(local_user='nobody')
            eq_(Connection('host', config=config).user, 'nobody')

        def user_may_be_given_explicitly(self):
            eq_(Connection('host', user='somebody').user, 'somebody')

        def port_defaults_to_configuration_default_port(self):
            config = Configuration(default_port=2222)
            eq_(Connection('host', config=config).port, 2222)

        def port_may_be_given_explicitly(self):
            skip()
