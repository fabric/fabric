from invoke import Collection, Context
from invoke.parser import ParseResult, ParserContext, Argument
from fabric import Executor, Task, Connection

from mock import Mock
from pytest import skip  # noqa


def _execute_task(val=None):
    hosts = Argument(name="hosts")
    hosts.value = val
    core_args = ParseResult([ParserContext(args=[hosts])])
    task = Mock()
    coll = Collection(mytask=Task(task))
    executor = Executor(coll, core=core_args)
    executor.execute("mytask")
    return task


class Executor_:
    class expand_calls:
        class hosts_flag_empty:
            def no_parameterization_is_done(self):
                task = _execute_task()
                assert task.call_count == 1
                assert isinstance(task.call_args[0][0], Context)

        class hosts_flag_set:
            def parameterization_per_host(self):
                task = _execute_task(val="host1,host2,host3")
                assert task.call_count == 3
                assert isinstance(task.call_args[0][0], Connection)

            def post_tasks_happen_once_only(self):
                skip()

        class remainder:
            def raises_NothingToDo_when_no_hosts(self):
                skip()

            def creates_anonymous_call_per_host(self):
                skip()

        class dedupe:
            def deduplication_not_performed(self):
                skip()

        class parameterize:
            def always_generates_ConnectionCall_with_host_attr(self):
                skip()


# TODO: add new tests for desired interpretation of @hosts-driven .hosts attrs
# on Task objs (similarly unit-style)
