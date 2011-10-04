from __future__ import with_statement

from functools import wraps

from fabric import state
from fabric.utils import abort
from fabric.context_managers import settings


class Task(object):
    """
    Abstract base class for objects wishing to be picked up as Fabric tasks.

    Instances of subclasses will be treated as valid tasks when present in
    fabfiles loaded by the :doc:`fab </usage/fab>` tool.

    For details on how to implement and use `~fabric.tasks.Task` subclasses,
    please see the usage documentation on :ref:`new-style tasks
    <new-style-tasks>`.

    .. versionadded:: 1.1
    """
    name = 'undefined'
    use_task_objects = True
    aliases = None
    is_default = False

    # TODO: make it so that this wraps other decorators as expected
    def __init__(self, alias=None, aliases=None, default=False,
        *args, **kwargs):
        if alias is not None:
            self.aliases = [alias, ]
        if aliases is not None:
            self.aliases = aliases
        self.is_default = default

    def run(self):
        raise NotImplementedError


class WrappedCallableTask(Task):
    """
    Wraps a given callable transparently, while marking it as a valid Task.

    Generally used via `@task <~fabric.decorators.task>` and not directly.

    .. versionadded:: 1.1
    """
    def __init__(self, callable, *args, **kwargs):
        super(WrappedCallableTask, self).__init__(*args, **kwargs)
        self.wrapped = callable
        self.__name__ = self.name = callable.__name__
        self.__doc__ = callable.__doc__

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def __getattr__(self, k):
        return getattr(self.wrapped, k)


def execute(task, *args, **kwargs):
    """
    Execute ``task`` (callable or name), honoring host/role decorators, etc.

    ``task`` may be an actual callable object, or it may be a registered task
    name, which is used to look up a callable just as if the name had been
    given on the command line (including :ref:`namespaced tasks <namespaces>`,
    e.g. ``"deploy.migrate"``.

    The task will then be executed once per host in its host list, which is
    (again) assembled in the same manner as CLI-specified tasks: drawing from
    :option:`-H`, :ref:`env.hosts <hosts>`, the `~fabric.decorators.hosts` or
    `~fabric.decorators.roles` decorators, and so forth.

    ``host``, ``hosts``, ``role`` and ``roles`` kwargs will be stripped out of
    the final call, and used to set the task's host list, as if they had been
    specified on the command line like e.g. ``fab taskname:host=hostname``.

    Any other arguments or keyword arguments will be passed verbatim into
    ``task`` when it is called, so ``execute(mytask, 'arg1', kwarg1='value')``
    will (once per host) invoke ``mytask('arg1', kwarg1='value')``.

    .. seealso::
        :ref:`The execute usage docs <execute>`, for an expanded explanation
        and some examples.

    .. versionadded:: 1.3
    """
    # Obtain task
    if not callable(task):
        try:
            task = state.commands[task]
        except KeyError:
            abort("Tried to execute(%r) but %r is not a valid task name" % (
                task, task
            ))
    # Filter out hosts/roles kwargs
    new_kwargs = {}
    hosts = []
    roles = []
    for key, value in kwargs.iteritems():
        if key == 'hosts':
            hosts = value
        elif key == 'roles':
            roles = value
        else:
            new_kwargs[key] = value
    # Call on local host list
    if hosts:
        for host in hosts:
            with settings(host_string=host):
                task(*args, **new_kwargs)
    else:
        task(*args, **new_kwargs)
