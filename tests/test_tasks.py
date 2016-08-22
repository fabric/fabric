from __future__ import with_statement

from fudge import Fake, patched_context, with_fakes
import unittest
from nose.tools import raises, ok_
import random
import sys

import fabric
from fabric.tasks import WrappedCallableTask, execute, Task, get_task_details
from fabric.main import display_command
from fabric.api import run, env, settings, hosts, roles, hide, parallel, task, runs_once, serial
from fabric.exceptions import NetworkError

from utils import eq_, FabricTest, aborts, mock_streams, support
from server import server


def test_base_task_provides_undefined_name():
    task = Task()
    eq_("undefined", task.name)

@raises(NotImplementedError)
def test_base_task_raises_exception_on_call_to_run():
    task = Task()
    task.run()

class TestWrappedCallableTask(unittest.TestCase):
    def test_passes_unused_args_to_parent(self):
        args = [i for i in range(random.randint(1, 10))]

        def foo(): pass
        try:
            WrappedCallableTask(foo, *args)
        except TypeError:
            msg = "__init__ raised a TypeError, meaning args weren't handled"
            self.fail(msg)

    def test_passes_unused_kwargs_to_parent(self):
        random_range = range(random.randint(1, 10))
        kwargs = dict([("key_%s" % i, i) for i in random_range])

        def foo(): pass
        try:
            WrappedCallableTask(foo, **kwargs)
        except TypeError:
            self.fail(
                "__init__ raised a TypeError, meaning kwargs weren't handled")

    def test_allows_any_number_of_args(self):
        args = [i for i in range(random.randint(0, 10))]
        def foo(): pass
        WrappedCallableTask(foo, *args)

    def test_allows_any_number_of_kwargs(self):
        kwargs = dict([("key%d" % i, i) for i in range(random.randint(0, 10))])
        def foo(): pass
        WrappedCallableTask(foo, **kwargs)

    def test_run_is_wrapped_callable(self):
        def foo(): pass
        task = WrappedCallableTask(foo)
        eq_(task.wrapped, foo)

    def test_name_is_the_name_of_the_wrapped_callable(self):
        def foo(): pass
        foo.__name__ = "random_name_%d" % random.randint(1000, 2000)
        task = WrappedCallableTask(foo)
        eq_(task.name, foo.__name__)

    def test_name_can_be_overridden(self):
        def foo(): pass
        eq_(WrappedCallableTask(foo).name, 'foo')
        eq_(WrappedCallableTask(foo, name='notfoo').name, 'notfoo')

    def test_reads_double_under_doc_from_callable(self):
        def foo(): pass
        foo.__doc__ = "Some random __doc__: %d" % random.randint(1000, 2000)
        task = WrappedCallableTask(foo)
        eq_(task.__doc__, foo.__doc__)

    def test_dispatches_to_wrapped_callable_on_run(self):
        random_value = "some random value %d" % random.randint(1000, 2000)
        def foo(): return random_value
        task = WrappedCallableTask(foo)
        eq_(random_value, task())

    def test_passes_all_regular_args_to_run(self):
        def foo(*args): return args
        random_args = tuple(
            [random.randint(1000, 2000) for i in range(random.randint(1, 5))]
        )
        task = WrappedCallableTask(foo)
        eq_(random_args, task(*random_args))

    def test_passes_all_keyword_args_to_run(self):
        def foo(**kwargs): return kwargs
        random_kwargs = {}
        for i in range(random.randint(1, 5)):
            random_key = ("foo", "bar", "baz", "foobar", "barfoo")[i]
            random_kwargs[random_key] = random.randint(1000, 2000)
        task = WrappedCallableTask(foo)
        eq_(random_kwargs, task(**random_kwargs))

    def test_calling_the_object_is_the_same_as_run(self):
        random_return = random.randint(1000, 2000)
        def foo(): return random_return
        task = WrappedCallableTask(foo)
        eq_(task(), task.run())


class TestTask(unittest.TestCase):
    def test_takes_an_alias_kwarg_and_wraps_it_in_aliases_list(self):
        random_alias = "alias_%d" % random.randint(100, 200)
        task = Task(alias=random_alias)
        self.assertTrue(random_alias in task.aliases)

    def test_aliases_are_set_based_on_provided_aliases(self):
        aliases = ["a_%d" % i for i in range(random.randint(1, 10))]
        task = Task(aliases=aliases)
        self.assertTrue(all([a in task.aliases for a in aliases]))

    def test_aliases_are_None_by_default(self):
        task = Task()
        self.assertTrue(task.aliases is None)


# Reminder: decorator syntax, e.g.:
#     @foo
#     def bar():...
#
# is semantically equivalent to:
#     def bar():...
#     bar = foo(bar)
#
# this simplifies testing :)

def test_decorator_incompatibility_on_task():
    from fabric.decorators import task, hosts, runs_once, roles
    def foo(): return "foo"
    foo = task(foo)

    # since we aren't setting foo to be the newly decorated thing, its cool
    hosts('me@localhost')(foo)
    runs_once(foo)
    roles('www')(foo)

def test_decorator_closure_hiding():
    """
    @task should not accidentally destroy decorated attributes from @hosts/etc
    """
    from fabric.decorators import task, hosts
    def foo():
        print(env.host_string)
    foo = task(hosts("me@localhost")(foo))
    eq_(["me@localhost"], foo.hosts)



#
# execute()
#

def dict_contains(superset, subset):
    """
    Assert that all key/val pairs in dict 'subset' also exist in 'superset'
    """
    for key, value in subset.iteritems():
        ok_(key in superset)
        eq_(superset[key], value)


class TestExecute(FabricTest):
    @with_fakes
    def test_calls_task_function_objects(self):
        """
        should execute the passed-in function object
        """
        execute(Fake(callable=True, expect_call=True))

    @with_fakes
    def test_should_look_up_task_name(self):
        """
        should also be able to handle task name strings
        """
        name = 'task1'
        commands = {name: Fake(callable=True, expect_call=True)}
        with patched_context(fabric.state, 'commands', commands):
            execute(name)

    @with_fakes
    def test_should_handle_name_of_Task_object(self):
        """
        handle corner case of Task object referrred to by name
        """
        name = 'task2'
        class MyTask(Task):
            run = Fake(callable=True, expect_call=True)
        mytask = MyTask()
        mytask.name = name
        commands = {name: mytask}
        with patched_context(fabric.state, 'commands', commands):
            execute(name)

    @aborts
    def test_should_abort_if_task_name_not_found(self):
        """
        should abort if given an invalid task name
        """
        execute('thisisnotavalidtaskname')

    def test_should_not_abort_if_task_name_not_found_with_skip(self):
        """
        should not abort if given an invalid task name
        and skip_unknown_tasks in env
        """
        env.skip_unknown_tasks = True
        execute('thisisnotavalidtaskname')
        del env['skip_unknown_tasks']

    @with_fakes
    def test_should_pass_through_args_kwargs(self):
        """
        should pass in any additional args, kwargs to the given task.
        """
        task = (
            Fake(callable=True, expect_call=True)
            .with_args('foo', biz='baz')
        )
        execute(task, 'foo', biz='baz')

    @with_fakes
    def test_should_honor_hosts_kwarg(self):
        """
        should use hosts kwarg to set run list
        """
        # Make two full copies of a host list
        hostlist = ['a', 'b', 'c']
        hosts = hostlist[:]
        # Side-effect which asserts the value of env.host_string when it runs
        def host_string():
            eq_(env.host_string, hostlist.pop(0))
        task = Fake(callable=True, expect_call=True).calls(host_string)
        with hide('everything'):
            execute(task, hosts=hosts)

    def test_should_honor_hosts_decorator(self):
        """
        should honor @hosts on passed-in task objects
        """
        # Make two full copies of a host list
        hostlist = ['a', 'b', 'c']
        @hosts(*hostlist[:])
        def task():
            eq_(env.host_string, hostlist.pop(0))
        with hide('running'):
            execute(task)

    def test_should_honor_roles_decorator(self):
        """
        should honor @roles on passed-in task objects
        """
        # Make two full copies of a host list
        roledefs = {'role1': ['a', 'b', 'c']}
        role_copy = roledefs['role1'][:]
        @roles('role1')
        def task():
            eq_(env.host_string, role_copy.pop(0))
        with settings(hide('running'), roledefs=roledefs):
            execute(task)

    @with_fakes
    def test_should_set_env_command_to_string_arg(self):
        """
        should set env.command to any string arg, if given
        """
        name = "foo"
        def command():
            eq_(env.command, name)
        task = Fake(callable=True, expect_call=True).calls(command)
        with patched_context(fabric.state, 'commands', {name: task}):
            execute(name)

    @with_fakes
    def test_should_set_env_command_to_name_attr(self):
        """
        should set env.command to TaskSubclass.name if possible
        """
        name = "foo"
        def command():
            eq_(env.command, name)
        task = (
            Fake(callable=True, expect_call=True)
            .has_attr(name=name)
            .calls(command)
        )
        execute(task)

    @with_fakes
    def test_should_set_all_hosts(self):
        """
        should set env.all_hosts to its derived host list
        """
        hosts = ['a', 'b']
        roledefs = {'r1': ['c', 'd']}
        roles = ['r1']
        exclude_hosts = ['a']
        def command():
            eq_(set(env.all_hosts), set(['b', 'c', 'd']))
        task = Fake(callable=True, expect_call=True).calls(command)
        with settings(hide('everything'), roledefs=roledefs):
            execute(
                task, hosts=hosts, roles=roles, exclude_hosts=exclude_hosts
            )

    @mock_streams('stdout')
    def test_should_print_executing_line_per_host(self):
        """
        should print "Executing" line once per host
        """
        def task():
            pass
        execute(task, hosts=['host1', 'host2'])
        eq_(sys.stdout.getvalue(), """[host1] Executing task 'task'
[host2] Executing task 'task'
""")

    @mock_streams('stdout')
    def test_should_not_print_executing_line_for_singletons(self):
        """
        should not print "Executing" line for non-networked tasks
        """
        def task():
            pass
        with settings(hosts=[]): # protect against really odd test bleed :(
            execute(task)
        eq_(sys.stdout.getvalue(), "")

    def test_should_return_dict_for_base_case(self):
        """
        Non-network-related tasks should return a dict w/ special key
        """
        def task():
            return "foo"
        eq_(execute(task), {'<local-only>': 'foo'})

    @server(port=2200)
    @server(port=2201)
    def test_should_return_dict_for_serial_use_case(self):
        """
        Networked but serial tasks should return per-host-string dict
        """
        ports = [2200, 2201]
        hosts = map(lambda x: '127.0.0.1:%s' % x, ports)
        def task():
            run("ls /simple")
            return "foo"
        with hide('everything'):
            eq_(execute(task, hosts=hosts), {
                '127.0.0.1:2200': 'foo',
                '127.0.0.1:2201': 'foo'
            })

    @server()
    def test_should_preserve_None_for_non_returning_tasks(self):
        """
        Tasks which don't return anything should still show up in the dict
        """
        def local_task():
            pass
        def remote_task():
            with hide('everything'):
                run("ls /simple")
        eq_(execute(local_task), {'<local-only>': None})
        with hide('everything'):
            eq_(
                execute(remote_task, hosts=[env.host_string]),
                {env.host_string: None}
            )

    def test_should_use_sentinel_for_tasks_that_errored(self):
        """
        Tasks which errored but didn't abort should contain an eg NetworkError
        """
        def task():
            run("whoops")
        host_string = 'localhost:1234'
        with settings(hide('everything'), skip_bad_hosts=True):
            retval = execute(task, hosts=[host_string])
        assert isinstance(retval[host_string], NetworkError)

    @server(port=2200)
    @server(port=2201)
    def test_parallel_return_values(self):
        """
        Parallel mode should still return values as in serial mode
        """
        @parallel
        @hosts('127.0.0.1:2200', '127.0.0.1:2201')
        def task():
            run("ls /simple")
            return env.host_string.split(':')[1]
        with hide('everything'):
            retval = execute(task)
        eq_(retval, {'127.0.0.1:2200': '2200', '127.0.0.1:2201': '2201'})

    @with_fakes
    def test_should_work_with_Task_subclasses(self):
        """
        should work for Task subclasses, not just WrappedCallableTask
        """
        class MyTask(Task):
            name = "mytask"
            run = Fake(callable=True, expect_call=True)
        mytask = MyTask()
        execute(mytask)

    @server(port=2200)
    @server(port=2201)
    def test_nested_execution_with_explicit_ports(self):
        """
        nested executions should work with defined ports
        """

        def expect_host_string_port():
            eq_(env.port, '2201')
            return "bar"

        def expect_env_port():
            eq_(env.port, '2202')

        def expect_per_host_config_port():
            eq_(env.port, '664')
            run = execute(expect_default_config_port, hosts=['some_host'])
            return run['some_host']

        def expect_default_config_port():
            # uses `Host *` in ssh_config
            eq_(env.port, '666')
            return "bar"

        def main_task():
            eq_(env.port, '2200')

            execute(expect_host_string_port, hosts=['localhost:2201'])

            with settings(port='2202'):
                execute(expect_env_port, hosts=['localhost'])

            with settings(
                use_ssh_config=True,
                ssh_config_path=support("ssh_config")
            ):
                run = execute(expect_per_host_config_port, hosts='myhost')

            return run['myhost']

        run = execute(main_task, hosts=['localhost:2200'])

        eq_(run['localhost:2200'], 'bar')


class TestExecuteEnvInteractions(FabricTest):
    def set_network(self):
        # Don't update env.host/host_string/etc
        pass

    @server(port=2200)
    @server(port=2201)
    def test_should_not_mutate_its_own_env_vars(self):
        """
        internal env changes should not bleed out, but task env changes should
        """
        # Task that uses a handful of features which involve env vars
        @parallel
        @hosts('username@127.0.0.1:2200', 'username@127.0.0.1:2201')
        def mytask():
            run("ls /simple")
        # Pre-assertions
        assertions = {
            'parallel': False,
            'all_hosts': [],
            'host': None,
            'hosts': [],
            'host_string': None
        }
        for key, value in assertions.items():
            eq_(env[key], value)
        # Run
        with hide('everything'):
            result = execute(mytask)
        eq_(len(result), 2)
        # Post-assertions
        for key, value in assertions.items():
            eq_(env[key], value)

    @server()
    def test_should_allow_task_to_modify_env_vars(self):
        @hosts('username@127.0.0.1:2200')
        def mytask():
            run("ls /simple")
            env.foo = "bar"
        with hide('everything'):
            execute(mytask)
        eq_(env.foo, "bar")
        eq_(env.host_string, None)


class TestTaskDetails(unittest.TestCase):
    def test_old_style_task_with_default_args(self):
        """
        __details__() should print docstr for old style task methods with default args
        """
        def task_old_style(arg1, arg2, arg3=None, arg4='yes'):
            '''Docstring'''
        details = get_task_details(task_old_style)
        eq_("Docstring\n"
            "Arguments: arg1, arg2, arg3=None, arg4='yes'",
            details)

    def test_old_style_task_without_default_args(self):
        """
        __details__() should print docstr for old style task methods without default args
        """

        def task_old_style(arg1, arg2):
            '''Docstring'''
        details = get_task_details(task_old_style)
        eq_("Docstring\n"
            "Arguments: arg1, arg2",
            details)

    def test_old_style_task_without_args(self):
        """
        __details__() should print docstr for old style task methods without args
        """

        def task_old_style():
            '''Docstring'''
        details = get_task_details(task_old_style)
        eq_("Docstring\n"
            "Arguments: ",
            details)

    def test_decorated_task(self):
        """
        __details__() should print docstr for method with any number and order of decorations
        """
        expected = "\n".join([
            "Docstring",
            "Arguments: arg1",
            ])

        @task
        def decorated_task(arg1):
            '''Docstring'''

        actual = decorated_task.__details__()
        eq_(expected, actual)

        @runs_once
        @task
        def decorated_task1(arg1):
            '''Docstring'''

        actual = decorated_task1.__details__()
        eq_(expected, actual)

        @runs_once
        @serial
        @task
        def decorated_task2(arg1):
            '''Docstring'''

        actual = decorated_task2.__details__()
        eq_(expected, actual)

    def test_subclassed_task(self):
        """
        __details__() should print docstr for subclassed task methods with args
        """

        class SpecificTask(Task):
            def run(self, arg1, arg2, arg3):
                '''Docstring'''
        eq_("Docstring\n"
            "Arguments: self, arg1, arg2, arg3",
            SpecificTask().__details__())

    @mock_streams('stdout')
    def test_multiline_docstring_indented_correctly(self):
        """
        display_command() should properly indent docstr for old style task methods
        """

        def mytask(arg1):
            """
            This is a multi line docstring.

            For reals.
            """
        try:
            with patched_context(fabric.state, 'commands', {'mytask': mytask}):
                display_command('mytask')
        except SystemExit: # ugh
            pass
        eq_(
            sys.stdout.getvalue(),
"""Displaying detailed information for task 'mytask':

    This is a multi line docstring.
    
    For reals.
    
    Arguments: arg1

"""
        )
