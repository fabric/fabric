
class Task(object):
    """
    A simple object who's instance can be used to decorate tasks inside a
    fabfile to explicitly define what should be a callable task.

    The key piece of this is the property `is_fabric_task`, which is all the
    decorator does to signify a function is a task.

    For convenience, you generally import `fabric.decorators.task` to
    explicitly state tasks in a fabfile.  You can subclass this to provide
    additional behavior while registering a task.
    """
    is_fabric_task = True

    def __call__(self, *args, **kwargs):
        pass


