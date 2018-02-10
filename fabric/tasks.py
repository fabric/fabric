
from invoke.tasks import BaseTask, Task as LocalTask, task as local_task
from .connection import Connection

__all__ = ['LocalTask', 'Task', 'local_task', 'task']


class Task(BaseTask):
    context_class = Connection


def task(*args, **kwargs):
    # @task -- no options were (probably) given.
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], Task):
        return Task(args[0], **kwargs)

    def inner(obj):
        # @task(pre, tasks, here)
        if args:
            return Task(obj, pre=args, **kwargs)
        # @task(options)
        else:
            return Task(obj, **kwargs)
    return inner
