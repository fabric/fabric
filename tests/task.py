# NOTE: named task.py, not tasks.py, to avoid some occasional pytest weirdness

from mock import Mock
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
        skip()


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
        def values_may_be_connection_first_posarg_strings(self):
            skip()

        def values_may_be_Connection_constructor_kwarg_dicts(self):
            skip()

        def values_may_be_mixed(self):
            skip()


class ConnectionCall_:
    class str:
        "___str__"

        def includes_host_attribute(self):
            def mytask(c):
                pass

            call = ConnectionCall(fabric.Task(body=mytask))
            call.host = "user@host"
            expected = "<ConnectionCall 'mytask', args: (), kwargs: {}, host='user@host'>"  # noqa
            assert str(call) == expected
