from contextlib import contextmanager
import fudge
import unittest
from nose.tools import eq_, raises
import random

from fabric import tasks
from fabric.tasks import WrappedCallableTask

def test_base_task_provides_undefined_name():
    task = tasks.Task()
    eq_("undefined", task.name)

@raises(NotImplementedError)
def test_base_task_raises_exception_on_call_to_run():
    task = tasks.Task()
    task.run()

class TestWrappedCallableTask(unittest.TestCase):
    def test_passes_unused_args_to_parent(self):
        args = [i for i in range(random.randint(1, 10))]

        def foo(): pass
        try:
            task = WrappedCallableTask(foo, *args)
        except TypeError:
            msg = "__init__ raised a TypeError, meaning args weren't handled"
            self.fail(msg)

    def test_passes_unused_kwargs_to_parent(self):
        random_range = range(random.randint(1, 10))
        kwargs = dict([("key_%s" % i, i) for i in random_range])

        def foo(): pass
        try:
            task = WrappedCallableTask(foo, **kwargs)
        except TypeError:
            self.fail(
                "__init__ raised a TypeError, meaning kwargs weren't handled")



    def test_allows_any_number_of_args(self):
        args = [i for i in range(random.randint(0, 10))]
        def foo(): pass
        task = tasks.WrappedCallableTask(foo, *args)

    def test_allows_any_number_of_kwargs(self):
        kwargs = dict([("key%d" % i, i) for i in range(random.randint(0, 10))])
        def foo(): pass
        task = tasks.WrappedCallableTask(foo, **kwargs)

    def test_run_is_wrapped_callable(self):
        def foo(): pass

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(task.wrapped, foo)

    def test_name_is_the_name_of_the_wrapped_callable(self):
        def foo(): pass
        foo.__name__ = "random_name_%d" % random.randint(1000, 2000)

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(task.name, foo.__name__)

    def test_reads_double_under_doc_from_callable(self):
        def foo(): pass
        foo.__doc__ = "Some random __doc__: %d" % random.randint(1000, 2000)

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(task.__doc__, foo.__doc__)

    def test_dispatches_to_wrapped_callable_on_run(self):
        random_value = "some random value %d" % random.randint(1000, 2000)
        def foo(): return random_value

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(random_value, task())

    def test_passes_all_regular_args_to_run(self):
        def foo(*args): return args

        random_args = tuple([random.randint(1000, 2000) for i in range(random.randint(1, 5))])
        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(random_args, task(*random_args))

    def test_passes_all_keyword_args_to_run(self):
        def foo(**kwargs): return kwargs

        random_kwargs = {}
        for i in range(random.randint(1, 5)):
            random_key = ("foo", "bar", "baz", "foobar", "barfoo")[i]
            random_kwargs[random_key] = random.randint(1000, 2000)

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(random_kwargs, task(**random_kwargs))

    def test_calling_the_object_is_the_same_as_run(self):
        random_return = random.randint(1000, 2000)
        def foo(): return random_return

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(task(), task.run())


class TestTask(unittest.TestCase):
    def test_takes_an_alias_kwarg_and_wraps_it_in_aliases_list(self):
        random_alias = "alias_%d" % random.randint(100, 200)
        task = tasks.Task(alias=random_alias)
        self.assertTrue(random_alias in task.aliases)

    def test_aliases_are_set_based_on_provided_aliases(self):
        aliases = ["a_%d" % i for i in range(random.randint(1, 10))]
        task = tasks.Task(aliases=aliases)
        self.assertTrue(all([a in task.aliases for a in aliases]))

    def test_aliases_are_None_by_default(self):
        task = tasks.Task()
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
    from fabric.decorators import task, hosts
    def foo(): print env.host_string
    foo = hosts("me@localhost")(foo)
    foo = task(foo)

    # this broke in the old way, due to closure stuff hiding in the
    # function, but task making an object
    eq_(["me@localhost"], foo.hosts)
