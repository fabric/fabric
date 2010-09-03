from functools import wraps

class Task(object):
    """
    Base Task class, from which all class-based Tasks should extend.

    This class is used to provide a way to test whether a task is really
    a task or not.  It provides no functionality and should not used
    directly.
    """
    name = 'undefined'
    use_decorated = False

    def run(self):
        raise NotImplementedError


class WrappedCallableTask(Task):
    """
    Task for wrapping some sort of callable in a Task object.

    Generally used via the `@task` decorator.
    """
    def __init__(self, callable):
        super(WrappedCallableTask, self).__init__()
        self.use_decorated = True
        self.wrapped = callable
        self.__name__ = self.name = callable.__name__
        self.__doc__ = callable.__doc__

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def __getattr__(self, k):
        return getattr(self.wrapped, k)
