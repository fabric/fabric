import unittest
from nose.tools import eq_, raises
import random

from fabric import tasks

def test_base_task_provides_undefined_name():
    task = tasks.Task()
    eq_("undefined", task.name)

@raises(NotImplementedError)
def test_base_task_raises_exception_on_call_to_executable():
    task = tasks.Task()
    task.executable()

class TestOfWrappedCallableTask(unittest.TestCase):
    def test_executable_is_wrapped_callable(self):
        def foo(): pass

        task = tasks.WrappedCallableTask(foo)
        self.assertEqual(task.executable, foo)

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

