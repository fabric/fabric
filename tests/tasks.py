from pytest import raises

from invoke import Context
from fabric import task, Task, Connection


class task_:
    "@task"

    def return_type_is_correctly_subclassed(self):
        @task
        def fn1(ctx):
            pass

        @task(name='foo')
        def fn2(ctx):
            pass

        assert isinstance(fn1, Task)
        assert isinstance(fn2, Task)


class Task_:
    class callability:
        def setup(self):
            @task
            def mytask(ctx):
                pass
            self.mytask = mytask

        def expects_Connection_as_first_arg(self):
            self.mytask(Connection(host='localhost'))

        def errors_if_first_arg_is_Context(self):
            with raises(TypeError):
                self.mytask(Context())
