from invoke import Collection, Context
from invoke.parser import ParseResult, ParserContext, Argument
from fabric import Executor, Task, Connection
from fabric.exceptions import NothingToDo

from mock import Mock
from pytest import skip, raises  # noqa


def _execute(val=None, post=None, remainder=""):
    post_tasks = []
    if post is not None:
        post_tasks.append(post)
    hosts = Argument(name="hosts")
    hosts.value = val
    core_args = ParseResult([ParserContext(args=[hosts])])
    core_args.remainder = remainder
    task = Mock()
    coll = Collection(mytask=Task(task, post=post_tasks))
    executor = Executor(coll, core=core_args)
    executor.execute("mytask")
    return task


class Executor_:
    class expand_calls:
        class hosts_flag_empty:
            def no_parameterization_is_done(self):
                task = _execute()
                assert task.call_count == 1
                assert isinstance(task.call_args[0][0], Context)

        class hosts_flag_set:
            def parameterization_per_host(self):
                task = _execute(val="host1,host2,host3")
                assert task.call_count == 3
                assert isinstance(task.call_args[0][0], Connection)

            def post_tasks_happen_once_only(self):
                post = Mock()
                task = _execute(val="host1,host2,host3", post=Task(post))
                assert task.call_count == 3
                assert post.call_count == 1

        class remainder:
            def raises_NothingToDo_when_no_hosts(self):
                with raises(NothingToDo):
                    _execute(remainder="whatever")

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
