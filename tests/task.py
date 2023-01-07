# NOTE: named task.py, not tasks.py, to avoid some occasional pytest weirdness

from unittest.mock import Mock
from pytest import skip  # noqa

import fabric
from fabric.tasks import ConnectionCall


class Task_:
    def accepts_Invoke_level_init_kwargs(self):
        # Arbitrarily selected list of invoke-level kwargs...
        def body(c, parts):
            "I am a docstring"
            pass

        t = fabric.Task(
            body=body,
            name="dadbod",
            aliases=["heavenly", "check", "shop"],
            default=True,
            help={"parts": "See: the sum of"},
            iterable=["parts"],
        )
        assert t.body is body
        assert t.__doc__ == "I am a docstring"
        assert t.name == "dadbod"
        assert "heavenly" in t.aliases
        assert t.is_default
        assert "parts" in t.help
        assert "parts" in t.iterable

    def allows_hosts_kwarg(self):
        # NOTE: most tests are below, in @task tests
        assert fabric.Task(Mock(), hosts=["user@host"]).hosts == ["user@host"]


class task_:
    def accepts_Invoke_level_kwargs(self):
        # Arbitrarily selected list of invoke-level kwargs...
        def body(c, parts):
            "I am a docstring"
            pass

        # Faux @task()
        t = fabric.task(
            name="dadbod",
            aliases=["heavenly", "check", "shop"],
            default=True,
            help={"parts": "See: the sum of"},
            iterable=["parts"],
        )(body)
        assert t.body is body
        assert t.__doc__ == "I am a docstring"
        assert t.name == "dadbod"
        assert "heavenly" in t.aliases
        assert t.is_default
        assert "parts" in t.help
        assert "parts" in t.iterable

    def returns_Fabric_level_Task_instance(self):
        assert isinstance(fabric.task(Mock()), fabric.Task)

    def does_not_touch_klass_kwarg_if_explicitly_given(self):
        # Otherwise sub-subclassers would be screwed, yea?
        class SubFabTask(fabric.Task):
            pass

        assert isinstance(fabric.task(klass=SubFabTask)(Mock()), SubFabTask)

    class hosts_kwarg:
        # NOTE: these don't currently test anything besides "the value given is
        # attached as .hosts" but they guard against regressions and ensures
        # things work as documented, even if Executor is what really cares.
        def _run(self, hosts):
            @fabric.task(hosts=hosts)
            def mytask(c):
                pass

            assert mytask.hosts == hosts

        def values_may_be_connection_first_posarg_strings(self):
            self._run(["host1", "user@host2", "host3:2222"])

        def values_may_be_Connection_constructor_kwarg_dicts(self):
            self._run(
                [
                    {"host": "host1"},
                    {"host": "host2", "user": "user"},
                    {"host": "host3", "port": 2222},
                ]
            )

        def values_may_be_mixed(self):
            self._run([{"host": "host1"}, "user@host2"])


def _dummy(c):
    pass


class ConnectionCall_:
    class init:
        "__init__"

        def inherits_regular_kwargs(self):
            t = fabric.Task(_dummy)
            call = ConnectionCall(
                task=t,
                called_as="meh",
                args=["5"],
                kwargs={"kwarg": "val"},
                init_kwargs={},  # whatever
            )
            assert call.task is t
            assert call.called_as == "meh"
            assert call.args == ["5"]
            assert call.kwargs["kwarg"] == "val"

        def extends_with_init_kwargs_kwarg(self):
            call = ConnectionCall(
                task=fabric.Task(_dummy),
                init_kwargs={"host": "server", "port": 2222},
            )
            assert call.init_kwargs["port"] == 2222

    class str:
        "___str__"

        def includes_init_kwargs_host_value(self):
            call = ConnectionCall(
                fabric.Task(body=_dummy),
                init_kwargs=dict(host="host", user="user"),
            )
            # TODO: worth using some subset of real Connection repr() in here?
            # For now, just stick with hostname.
            expected = "<ConnectionCall '_dummy', args: (), kwargs: {}, host='host'>"  # noqa
            assert str(call) == expected
