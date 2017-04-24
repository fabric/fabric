from mock import Mock, patch, call
from spec import Spec, eq_, ok_, raises

from fabric import Connection, Group, SerialGroup, ThreadingGroup, GroupResult
from fabric.group import thread_worker
from fabric.exceptions import GroupException

from invoke import task


class Group_(Spec):
    class init:
        "__init__"
        def may_be_empty(self):
            eq_(len(Group()), 0)

        def takes_splat_arg_of_host_strings(self):
            g = Group('foo', 'bar')
            eq_(g[0].host, 'foo')
            eq_(g[1].host, 'bar')

    class from_connections:
        def inits_from_iterable_of_Connections(self):
            g = Group.from_connections((Connection('foo'), Connection('bar')))
            eq_(len(g), 2)
            eq_(g[1].host, 'bar')

    def acts_like_an_iterable_of_Connections(self):
        g = Group('foo', 'bar', 'biz')
        eq_(g[0].host, 'foo')
        eq_(g[-1].host, 'biz')
        eq_(len(g), 3)
        for c in g:
            ok_(isinstance(c, Connection))

    class run:
        @raises(NotImplementedError)
        def not_implemented_in_base_class(self):
            Group().run()


def _make_serial_tester(cxns, index, args, kwargs):
    args = args[:]
    kwargs = kwargs.copy()
    def tester(*a, **k): # Don't care about doing anything with our own args.
        predecessors = cxns[:index]
        successors = cxns[index + 1:]
        for predecessor in predecessors:
            predecessor.run.assert_called_with(*args, **kwargs)
        for successor in successors:
            ok_(not successor.run.called)
    return tester

class SerialGroup_(Spec):
    class run:
        def executes_arguments_on_contents_run_serially(self):
            "executes arguments on contents' run() serially"
            cxns = [Connection(x) for x in ('host1', 'host2', 'host3')]
            args = ("command",)
            kwargs = {'hide': True, 'warn': True}
            for index, cxn in enumerate(cxns):
                side_effect = _make_serial_tester(cxns, index, args, kwargs)
                cxn.run = Mock(side_effect=side_effect)
            g = SerialGroup.from_connections(cxns)
            g.run(*args, **kwargs)
            # Sanity check, e.g. in case none of them were actually run
            for cxn in cxns:
                cxn.run.assert_called_with(*args, **kwargs)

        def errors_in_execution_capture_and_continue_til_end(self):
            cxns = [Mock(name=x) for x in ('host1', 'host2', 'host3')]
            class OhNoz(Exception):
                pass
            onoz = OhNoz()
            cxns[1].run.side_effect = onoz
            g = SerialGroup.from_connections(cxns)
            try:
                g.run("whatever", hide=True)
            except GroupException as e:
                result = e.result
            else:
                assert False, "Did not raise GroupException!"
            succeeded = {
                cxns[0]: cxns[0].run.return_value,
                cxns[2]: cxns[2].run.return_value,
            }
            failed = {
                cxns[1]: onoz,
            }
            expected = succeeded.copy()
            expected.update(failed)
            eq_(result, expected)
            eq_(result.succeeded, succeeded)
            eq_(result.failed, failed)

        def returns_results_mapping(self):
            cxns = [Mock(name=x) for x in ('host1', 'host2', 'host3')]
            g = SerialGroup.from_connections(cxns)
            result = g.run("whatever", hide=True)
            ok_(isinstance(result, GroupResult))
            expected = {}
            for cxn in cxns:
                expected[cxn] = cxn.run.return_value
            eq_(result, expected)
            eq_(result.succeeded, expected)
            eq_(result.failed, {})

    class execute:
        def executes_task_with_args_serially(self):
            "executes task with arguments serially"
            @task
            def task_function(ctx, command, keyword=None):
                return ctx.run(command, keyword=keyword)
            cxns = [Connection(x) for x in ('host1', 'host2', 'host3')]
            args = ("command",)
            task_kwargs = {'keyword': True}
            kwargs = {'hide': True, 'warn': True}
            kwargs.update(task_kwargs)
            for index, cxn in enumerate(cxns):
                side_effect = _make_serial_tester(
                    cxns,
                    index,
                    args,
                    task_kwargs
                )
                cxn.run = Mock(side_effect=side_effect)
            g = SerialGroup.from_connections(cxns)
            g.execute(task_function, *args, **kwargs)
            for cxn in cxns:
                cxn.run.assert_called_with(*args, **task_kwargs)


class ThreadingGroup_(Spec):
    def setup(self):
        self.cxns = [Connection(x) for x in ('host1', 'host2', 'host3')]
        self.args = ("command",)
        self.kwargs = {'hide': True, 'warn': True}
        @task
        def task_function(ctx, command):
            return ctx.run(command)
        self.task_function = task_function

    class run:
        @patch('fabric.group.Queue')
        @patch('fabric.group.ExceptionHandlingThread')
        def executes_arguments_on_contents_run_via_threading(
            self, Thread, Queue,
        ):
            queue = Queue.return_value
            g = ThreadingGroup.from_connections(self.cxns)
            # Make sure .exception() doesn't yield truthy Mocks. Otherwise we
            # end up with 'exceptions' that cause errors due to all being the
            # same.
            Thread.return_value.exception.return_value = None
            g.run(*self.args, **self.kwargs)
            # Testing that threads were used the way we expect is mediocre but
            # I honestly can't think of another good way to assert "threading
            # was used & concurrency occurred"...
            instantiations = [
                call(
                    target=thread_worker,
                    kwargs=dict(
                        cxn=cxn,
                        task=None,
                        queue=queue,
                        args=self.args,
                        kwargs=self.kwargs,
                    ),
                )
                for cxn in self.cxns
            ]
            Thread.assert_has_calls(instantiations, any_order=True)
            # These ought to work as by default a Mock.return_value is a
            # singleton mock object
            expected = len(self.cxns)
            for name, got in (
                ('start', Thread.return_value.start.call_count),
                ('join', Thread.return_value.join.call_count)
            ):
                err = "Expected {0} calls to ExceptionHandlingThread.{1}, got {2}" # noqa
                err = err.format(expected, name, got)
                eq_(expected, got, err)

        @patch('fabric.group.Queue')
        def queue_used_to_return_results(self, Queue):
            # Regular, explicit, mocks for Connections
            cxns = [Mock(host=x) for x in ('host1', 'host2', 'host3')]
            # Set up Queue with enough behavior to work / assert
            queue = Queue.return_value
            # Ending w/ a True will terminate a while-not-empty loop
            queue.empty.side_effect = (False, False, False, True)
            fakes = [(x, x.run.return_value) for x in cxns]
            queue.get.side_effect = fakes[:]
            # Execute & inspect results
            g = ThreadingGroup.from_connections(cxns)
            results = g.run(*self.args, **self.kwargs)
            expected = {}
            for cxn in cxns:
                expected[cxn] = cxn.run.return_value
            eq_(results, expected)
            # Make sure queue was used as expected within worker &
            # ThreadingGroup.run()
            puts = [call(x) for x in fakes]
            queue.put.assert_has_calls(puts, any_order=True)
            ok_(queue.empty.called)
            gets = [call(block=False) for _ in cxns]
            queue.get.assert_has_calls(gets)

        def bubbles_up_errors_within_threads(self):
            # TODO: I feel like this is the first spot where a raw
            # ThreadException might need tweaks, at least presentation-wise,
            # since we're no longer dealing with truly background threads (IO
            # workers and tunnels), but "middle-ground" threads the user is
            # kind of expecting (and which they might expect to encounter
            # failures).
            cxns = [Mock(host=x) for x in ('host1', 'host2', 'host3')]
            class OhNoz(Exception):
                pass
            onoz = OhNoz()
            cxns[1].run.side_effect = onoz
            g = ThreadingGroup.from_connections(cxns)
            try:
                g.run(*self.args, **self.kwargs)
            except GroupException as e:
                result = e.result
            else:
                assert False, "Did not raise GroupException!"
            succeeded = {
                cxns[0]: cxns[0].run.return_value,
                cxns[2]: cxns[2].run.return_value,
            }
            failed = {
                cxns[1]: onoz,
            }
            expected = succeeded.copy()
            expected.update(failed)
            eq_(result, expected)
            eq_(result.succeeded, succeeded)
            eq_(result.failed, failed)

        def returns_results_mapping(self):
            # TODO: update if/when we implement ResultSet
            cxns = [Mock(name=x) for x in ('host1', 'host2', 'host3')]
            g = ThreadingGroup.from_connections(cxns)
            result = g.run("whatever", hide=True)
            ok_(isinstance(result, GroupResult))
            expected = {}
            for cxn in cxns:
                expected[cxn] = cxn.run.return_value
            eq_(result, expected)
            eq_(result.succeeded, expected)
            eq_(result.failed, {})

    class execute:
        @patch('fabric.group.Queue')
        @patch('fabric.group.ExceptionHandlingThread')
        def executes_task_with_args_via_threading(
            self, Thread, Queue,
        ):
            queue = Queue.return_value
            g = ThreadingGroup.from_connections(self.cxns)
            # Make sure .exception() doesn't yield truthy Mocks. Otherwise we
            # end up with 'exceptions' that cause errors due to all being the
            # same.
            Thread.return_value.exception.return_value = None
            g.execute(self.task_function, *self.args, **self.kwargs)
            # Testing that threads were used the way we expect is mediocre but
            # I honestly can't think of another good way to assert "threading
            # was used & concurrency occurred"...
            instantiations = [
                call(
                    target=thread_worker,
                    kwargs=dict(
                        cxn=cxn,
                        task=self.task_function,
                        queue=queue,
                        args=self.args,
                        kwargs=self.kwargs,
                    ),
                )
                for cxn in self.cxns
            ]
            Thread.assert_has_calls(instantiations, any_order=True)
            # These ought to work as by default a Mock.return_value is a
            # singleton mock object
            expected = len(self.cxns)
            for name, got in (
                ('start', Thread.return_value.start.call_count),
                ('join', Thread.return_value.join.call_count)
            ):
                err = "Expected {0} calls to ExceptionHandlingThread.{1}, got {2}" # noqa
                err = err.format(expected, name, got)
                eq_(expected, got, err)
