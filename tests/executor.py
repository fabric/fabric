from invoke import Collection, Context, Call, Task as InvokeTask
from invoke.parser import ParseResult, ParserContext, Argument
from fabric import Executor, Task, Connection
from fabric.executor import ConnectionCall
from fabric.exceptions import NothingToDo

from unittest.mock import Mock
from pytest import skip, raises  # noqa


def _get_executor(hosts_flag=None, hosts_kwarg=None, post=None, remainder=""):
    post_tasks = []
    if post is not None:
        post_tasks.append(post)
    hosts = Argument(name="hosts")
    if hosts_flag is not None:
        hosts.value = hosts_flag
    core_args = ParseResult([ParserContext(args=[hosts])])
    core_args.remainder = remainder
    body = Mock(pre=[], post=[])
    task = Task(body, post=post_tasks, hosts=hosts_kwarg)
    coll = Collection(mytask=task)
    return body, Executor(coll, core=core_args)


def _execute(**kwargs):
    invocation = kwargs.pop("invocation", ["mytask"])
    task, executor = _get_executor(**kwargs)
    executor.execute(*invocation)
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
                task = _execute(hosts_flag="host1,host2,host3")
                assert task.call_count == 3
                assert isinstance(task.call_args[0][0], Connection)

            def post_tasks_happen_once_only(self):
                post = Mock()
                task = _execute(
                    hosts_flag="host1,host2,host3", post=Task(post)
                )
                assert task.call_count == 3
                assert post.call_count == 1

        class hosts_attribute_on_task_objects:
            def parameterization_per_host(self):
                task = _execute(hosts_kwarg=["host1", "host2", "host3"])
                assert task.call_count == 3
                assert isinstance(task.call_args[0][0], Connection)

            def post_tasks_happen_once_only(self):
                post = Mock()
                task = _execute(
                    hosts_kwarg=["host1", "host2", "host3"], post=Task(post)
                )
                assert task.call_count == 3
                assert post.call_count == 1

            def may_give_Connection_kwargs_as_values(self):
                task = _execute(
                    hosts_kwarg=[
                        {"host": "host1"},
                        {"host": "host2", "user": "doge"},
                    ]
                )
                assert task.call_count == 2
                expected = [
                    Connection("host1"),
                    Connection("host2", user="doge"),
                ]
                assert [x[0][0] for x in task.call_args_list] == expected

        class Invoke_task_objects_without_hosts_attribute_still_work:
            def execution_happens_normally_without_parameterization(self):
                body = Mock(pre=[], post=[])
                coll = Collection(mytask=InvokeTask(body))
                hosts = Argument(name="hosts")
                core_args = ParseResult([ParserContext(args=[hosts])])
                # When #1824 present, this just blows up because no .hosts attr
                Executor(coll, core=core_args).execute("mytask")
                assert body.call_count == 1

            def hosts_flag_still_triggers_parameterization(self):
                body = Mock(pre=[], post=[])
                coll = Collection(mytask=InvokeTask(body))
                hosts = Argument(name="hosts")
                hosts.value = "host1,host2,host3"
                core_args = ParseResult([ParserContext(args=[hosts])])
                Executor(coll, core=core_args).execute("mytask")
                assert body.call_count == 3

        class hosts_flag_vs_attributes:
            def flag_wins(self):
                task = _execute(
                    hosts_flag="via-flag", hosts_kwarg=["via-kwarg"]
                )
                assert task.call_count == 1
                assert task.call_args[0][0] == Connection(host="via-flag")

        class remainder:
            def raises_NothingToDo_when_no_hosts(self):
                with raises(NothingToDo):
                    _execute(remainder="whatever")

            def creates_anonymous_call_per_host(self):
                # TODO: annoying to do w/o mucking around w/ our Executor class
                # more, and that stuff wants to change semi soon anyways when
                # we grow past --hosts; punting.
                skip()

        class dedupe:
            def deduplication_not_performed(self):
                task = _execute(invocation=["mytask", "mytask"])
                assert task.call_count == 2  # not 1

        class parameterize:
            def always_generates_ConnectionCall_with_host_attr(self):
                task, executor = _get_executor(hosts_flag="host1,host2,host3")
                calls = executor.expand_calls(calls=[Call(task)])
                assert len(calls) == 3
                assert all(isinstance(x, ConnectionCall) for x in calls)
                assert [x.init_kwargs["host"] for x in calls] == [
                    "host1",
                    "host2",
                    "host3",
                ]
