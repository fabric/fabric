from nose.tools import eq_, ok_
import fudge
from fudge import Fake, with_fakes
import random

from fabric import decorators, tasks
from fabric.state import env

def test_task_returns_an_instance_of_wrappedfunctask_object():
    def foo():
        pass
    task = decorators.task(foo)
    ok_(isinstance(task, tasks.WrappedCallableTask))

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

def test_with_settings_passes_env_vars_into_decorated_function():
    env.value = True
    random_return = random.randint(1000, 2000)
    def some_task():
        return env.value
    decorated_task = decorators.with_settings(value=random_return)(some_task)
    ok_(some_task(), msg="sanity check")
    eq_(random_return, decorated_task())


def test_will_invoked_whatever_class_you_provide():
    def foo(): pass
    fake = Fake()
    fake.expects("__init__").with_args(foo)
    fudge.clear_calls()
    fudge.clear_expectations()

    foo = decorators.task(foo, task_class=fake)

    fudge.verify()


def test_passes_args_to_the_task_class():
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
