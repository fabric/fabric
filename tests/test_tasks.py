from nose.tools import eq_
import random

from fabric import tasks

def test_decorated_functions_are_called():
    random_number = random.randint(10000, 20000)

    task = tasks.Task()
    @task
    def return_random_number():
        return random_number

    eq_(random_number, return_random_number())

