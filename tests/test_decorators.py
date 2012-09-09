from __future__ import with_statement

import random
import sys

from nose.tools import eq_, ok_, assert_true, assert_false, assert_equal
import fudge
from fudge import Fake, with_fakes, patched_context

from fabric import decorators, tasks
from fabric.state import env
import fabric # for patching fabric.state.xxx
from fabric.tasks import _parallel_tasks, requires_parallel, execute
from fabric.context_managers import lcd, settings, hide

from utils import mock_streams


#
# Support
#

def fake_function(*args, **kwargs):
    """
    Returns a ``fudge.Fake`` exhibiting function-like attributes.

    Passes in all args/kwargs to the ``fudge.Fake`` constructor. However, if
    ``callable`` or ``expect_call`` kwargs are not given, ``callable`` will be
    set to True by default.
    """
    # Must define __name__ to be compatible with function wrapping mechanisms
    # like @wraps().
    if 'callable' not in kwargs and 'expect_call' not in kwargs:
        kwargs['callable'] = True
    return Fake(*args, **kwargs).has_attr(__name__='fake')



#
# @task
#

def test_task_returns_an_instance_of_wrappedfunctask_object():
    def foo():
        pass
    task = decorators.task(foo)
    ok_(isinstance(task, tasks.WrappedCallableTask))


def test_task_will_invoke_provided_class():
    def foo(): pass
    fake = Fake()
    fake.expects("__init__").with_args(foo)
    fudge.clear_calls()
    fudge.clear_expectations()

    foo = decorators.task(foo, task_class=fake)

    fudge.verify()


def test_task_passes_args_to_the_task_class():
    random_vars = ("some text", random.randint(100, 200))
    def foo(): pass

    fake = Fake()
    fake.expects("__init__").with_args(foo, *random_vars)
    fudge.clear_calls()
    fudge.clear_expectations()

    foo = decorators.task(foo, task_class=fake, *random_vars)
    fudge.verify()


def test_passes_kwargs_to_the_task_class():
    random_vars = {
        "msg": "some text",
        "number": random.randint(100, 200),
    }
    def foo(): pass

    fake = Fake()
    fake.expects("__init__").with_args(foo, **random_vars)
    fudge.clear_calls()
    fudge.clear_expectations()

    foo = decorators.task(foo, task_class=fake, **random_vars)
    fudge.verify()


def test_integration_tests_for_invoked_decorator_with_no_args():
    r = random.randint(100, 200)
    @decorators.task()
    def foo():
        return r

    eq_(r, foo())


def test_integration_tests_for_decorator():
    r = random.randint(100, 200)
    @decorators.task(task_class=tasks.WrappedCallableTask)
    def foo():
        return r

    eq_(r, foo())


def test_original_non_invoked_style_task():
    r = random.randint(100, 200)
    @decorators.task
    def foo():
        return r

    eq_(r, foo())



#
# @runs_once
#

@with_fakes
def test_runs_once_runs_only_once():
    """
    @runs_once prevents decorated func from running >1 time
    """
    func = fake_function(expect_call=True).times_called(1)
    task = decorators.runs_once(func)
    for i in range(2):
        task()


def test_runs_once_returns_same_value_each_run():
    """
    @runs_once memoizes return value of decorated func
    """
    return_value = "foo"
    task = decorators.runs_once(fake_function().returns(return_value))
    for i in range(2):
        eq_(task(), return_value)


@decorators.runs_once
def single_run():
    pass

def test_runs_once():
    assert_false(hasattr(single_run, 'return_value'))
    single_run()
    assert_true(hasattr(single_run, 'return_value'))
    assert_equal(None, single_run())



#
# @serial / @parallel
#


@decorators.serial
def serial():
    pass

@decorators.serial
@decorators.parallel
def serial2():
    pass

@decorators.parallel
@decorators.serial
def serial3():
    pass

@decorators.parallel
def parallel():
    pass

@decorators.parallel(pool_size=20)
def parallel2():
    pass

fake_tasks = {
    'serial': serial,
    'serial2': serial2,
    'serial3': serial3,
    'parallel': parallel,
    'parallel2': parallel2,
}

def parallel_task_helper(actual_tasks, expected):
    commands_to_run = map(lambda x: [x], actual_tasks)
    with patched_context(fabric.state, 'commands', fake_tasks):
        eq_(_parallel_tasks(commands_to_run), expected)

def test_parallel_tasks():
    for desc, task_names, expected in (
        ("One @serial-decorated task == no parallelism",
            ['serial'], False),
        ("One @parallel-decorated task == parallelism",
            ['parallel'], True),
        ("One @parallel-decorated and one @serial-decorated task == paralellism",
            ['parallel', 'serial'], True),
        ("Tasks decorated with both @serial and @parallel count as @parallel",
            ['serial2', 'serial3'], True)
    ):
        parallel_task_helper.description = desc
        yield parallel_task_helper, task_names, expected
        del parallel_task_helper.description

def test_parallel_wins_vs_serial():
    """
    @parallel takes precedence over @serial when both are used on one task
    """
    ok_(requires_parallel(serial2))
    ok_(requires_parallel(serial3))

@mock_streams('stdout')
def test_global_parallel_honors_runs_once():
    """
    fab -P (or env.parallel) should honor @runs_once
    """
    @decorators.runs_once
    def mytask():
        print("yolo") # 'Carpe diem' for stupid people!
    with settings(hide('everything'), parallel=True):
        execute(mytask, hosts=['localhost', '127.0.0.1'])
    result = sys.stdout.getvalue()
    eq_(result, "yolo\n")
    assert result != "yolo\nyolo\n"


#
# @roles
#

@decorators.roles('test')
def use_roles():
    pass

def test_roles():
    assert_true(hasattr(use_roles, 'roles'))
    assert_equal(use_roles.roles, ['test'])



#
# @hosts
#

@decorators.hosts('test')
def use_hosts():
    pass

def test_hosts():
    assert_true(hasattr(use_hosts, 'hosts'))
    assert_equal(use_hosts.hosts, ['test'])



#
# @with_settings
#

def test_with_settings_passes_env_vars_into_decorated_function():
    env.value = True
    random_return = random.randint(1000, 2000)
    def some_task():
        return env.value
    decorated_task = decorators.with_settings(value=random_return)(some_task)
    ok_(some_task(), msg="sanity check")
    eq_(random_return, decorated_task())

def test_with_settings_with_other_context_managers():
    """
    with_settings() should take other context managers, and use them with other
    overrided key/value pairs.
    """
    env.testval1 = "outer 1"
    prev_lcwd = env.lcwd

    def some_task():
        eq_(env.testval1, "inner 1")
        ok_(env.lcwd.endswith("here")) # Should be the side-effect of adding cd to settings

    decorated_task = decorators.with_settings(
        lcd("here"),
        testval1="inner 1"
    )(some_task)
    decorated_task()

    ok_(env.testval1, "outer 1")
    eq_(env.lcwd, prev_lcwd)
