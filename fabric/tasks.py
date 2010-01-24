
class Task(object):
    """
    Base Task class, from which all class-based Tasks should extend.

    This class is used to provide a way to test whether a task is really
    a task or not.  It provides no functionality and should not used
    directly.
    """
    name = 'undefined'

    def executable(self):
        raise NotImplementedError


class WrappedCallableTask(Task):
    """
    Task for wrapping some sort of callable in a Task object.

    Generally used via the `@task` decorator.
    """
    def __init__(self, executable):
        self.executable = executable
        self.name = self.executable.__name__
        self.__doc__ = self.executable.__doc__

    def __call__(self):
        return self

