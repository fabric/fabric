from spec import Spec, skip, eq_

from fabric import Connection


class Connection_(Spec):
    class init:
        "__init__"

        def host_required(self):
            skip()

        def user_defaults_to_local_user(self):
            skip()

        def user_may_be_given_explicitly(self):
            skip()

        def port_defaults_to_22(self):
            # TODO: default to a configured value
            skip()

        def port_may_be_given_explicitly(self):
            skip()

    class run:
        def uses_runners_Remote_with_invoke_runner(self):
            "uses invoke.runner.run(runner=fabric.runners.Remote)"
            skip()

    class sudo:
        def uses_runners_Remote_with_invoke_runner(self):
            "uses invoke.runner.run(runner=fabric.runners.RemoteSudo)"
            skip()

    class put:
        # fabric1's put() copied?
        pass

    class get:
        # fabric's get() copied?
        pass
