import unittest
from nose.tools import eq_, raises
import random

from fabric import tasks

def test_base_task_provides_undefined_name():
    task = tasks.Task()
    eq_("undefined", task.name)

@raises(NotImplementedError)
def test_base_task_raises_exception_on_call_to_run():
    task = tasks.Task()
    task.run()

class TestOfWrappedCallableTask(unittest.TestCase):
    def test_run_is_wrapped_callable(self):
        def foo(): pass

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(task.run, foo)

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

