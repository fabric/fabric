from functools import wraps

class Task(object):
    """
    Abstract base class for objects wishing to be picked up as Fabric tasks.

    Instances of subclasses will be treated as valid tasks when present in
    fabfiles loaded by the "fab" tool.
    """
    name = 'undefined'
    use_task_objects = True

    # TODO: make it so that this wraps other decorators as expected

    def run(self):
        raise NotImplementedError


class WrappedCallableTask(Task):
    """
    Wraps a given callable transparently, while marking it as a valid Task.

    Generally used via the ``@task`` decorator and not directly.
    """
    def __init__(self, callable):
        super(WrappedCallableTask, self).__init__()
        self.wrapped = callable
        self.__name__ = self.name = callable.__name__
        self.__doc__ = callable.__doc__

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def __getattr__(self, k):
        return getattr(self.wrapped, k)
