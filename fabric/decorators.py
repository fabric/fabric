"""
Convenience decorators for use in fabfiles.
"""
from __future__ import with_statement

from functools import wraps
from Crypto import Random

from fabric import tasks
from .context_managers import settings


def task(*args, **kwargs):
    """
    Decorator declaring the wrapped function to be a new-style task.

    May be invoked as a simple, argument-less decorator (i.e. ``@task``) or
    with arguments customizing its behavior (e.g. ``@task(alias='myalias')``).

    Please see the :ref:`new-style task <task-decorator>` documentation for
    details on how to use this decorator.

    .. versionchanged:: 1.2
        Added the ``alias``, ``aliases``, ``task_class`` and ``default``
        keyword arguments. See :ref:`task-decorator-arguments` for details.
    """
    invoked = bool(not args or kwargs)
    task_class = kwargs.pop("task_class", tasks.WrappedCallableTask)
    if not invoked:
        func, args = args[0], ()

    def wrapper(func):
        return task_class(func, *args, **kwargs)

    return wrapper if invoked else wrapper(func)

def _wrap_as_new(original, new):
    if isinstance(original, tasks.Task):
        return tasks.WrappedCallableTask(new)
    return new


def _list_annotating_decorator(attribute, *values):
    def attach_list(func):
        @wraps(func)
        def inner_decorator(*args, **kwargs):
            return func(*args, **kwargs)
        _values = values
        # Allow for single iterable argument as well as *args
        if len(_values) == 1 and not isinstance(_values[0], basestring):
            _values = _values[0]
        setattr(inner_decorator, attribute, list(_values))
        # Don't replace @task new-style task objects with inner_decorator by
        # itself -- wrap in a new Task object first.
        inner_decorator = _wrap_as_new(func, inner_decorator)
        return inner_decorator
    return attach_list


def hosts(*host_list):
    """
    Decorator defining which host or hosts to execute the wrapped function on.

    For example, the following will ensure that, barring an override on the
    command line, ``my_func`` will be run on ``host1``, ``host2`` and
    ``host3``, and with specific users on ``host1`` and ``host3``::

        @hosts('user1@host1', 'host2', 'user2@host3')
        def my_func():
            pass

    `~fabric.decorators.hosts` may be invoked with either an argument list
    (``@hosts('host1')``, ``@hosts('host1', 'host2')``) or a single, iterable
    argument (``@hosts(['host1', 'host2'])``).

    Note that this decorator actually just sets the function's ``.hosts``
    attribute, which is then read prior to executing the function.

    .. versionchanged:: 0.9.2
        Allow a single, iterable argument (``@hosts(iterable)``) to be used
        instead of requiring ``@hosts(*iterable)``.
    """
    return _list_annotating_decorator('hosts', *host_list)


def roles(*role_list):
    """
    Decorator defining a list of role names, used to look up host lists.

    A role is simply defined as a key in `env` whose value is a list of one or
    more host connection strings. For example, the following will ensure that,
    barring an override on the command line, ``my_func`` will be executed
    against the hosts listed in the ``webserver`` and ``dbserver`` roles::

        env.roledefs.update({
            'webserver': ['www1', 'www2'],
            'dbserver': ['db1']
        })

        @roles('webserver', 'dbserver')
        def my_func():
            pass

    As with `~fabric.decorators.hosts`, `~fabric.decorators.roles` may be
    invoked with either an argument list or a single, iterable argument.
    Similarly, this decorator uses the same mechanism as
    `~fabric.decorators.hosts` and simply sets ``<function>.roles``.

    .. versionchanged:: 0.9.2
        Allow a single, iterable argument to be used (same as
        `~fabric.decorators.hosts`).
    """
    return _list_annotating_decorator('roles', *role_list)


def runs_once(func):
    """
    Decorator preventing wrapped function from running more than once.

    By keeping internal state, this decorator allows you to mark a function
    such that it will only run once per Python interpreter session, which in
    typical use means "once per invocation of the ``fab`` program".

    Any function wrapped with this decorator will silently fail to execute the
    2nd, 3rd, ..., Nth time it is called, and will return the value of the
    original run.

    .. warning::
        This decorator is not compatible with Fabric's :doc:`parallel execution
        mode </usage/parallel>`; when used alongside
        `~fabric.decorators.parallel` or :option:`-P`, or when decorating
        subtasks of parallel tasks, each parallel copy of the decorated task
        will itself run one time, resulting in multiple runs.
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        if not hasattr(decorated, 'return_value'):
            decorated.return_value = func(*args, **kwargs)
        return decorated.return_value
    decorated = _wrap_as_new(func, decorated)
    # Mark as serial (disables parallelism) and return
    return serial(decorated)


def serial(func):
    """
    Forces the wrapped function to always run sequentially, never in parallel.

    This decorator takes precedence over the global value of :ref:`env.parallel
    <env-parallel>`. However, if a task is decorated with both
    `~fabric.decorators.serial` *and* `~fabric.decorators.parallel`,
    `~fabric.decorators.parallel` wins.

    .. versionadded:: 1.3
    """
    if not getattr(func, 'parallel', False):
        func.serial = True
    return _wrap_as_new(func, func)


def parallel(pool_size=None):
    """
    Forces the wrapped function to run in parallel, instead of sequentially.

    This decorator takes precedence over the global value of :ref:`env.parallel
    <env-parallel>`. It also takes precedence over `~fabric.decorators.serial`
    if a task is decorated with both.

    .. versionadded:: 1.3
    """
    def real_decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # Required for ssh/PyCrypto to be happy in multiprocessing
            # (as far as we can tell, this is needed even with the extra such
            # calls in newer versions of the 'ssh' library.)
            Random.atfork()
            return func(*args, **kwargs)
        inner.parallel = True
        inner.serial = False
        inner.pool_size = pool_size
        return _wrap_as_new(func, inner)

    # Allow non-factory-style decorator use (@decorator vs @decorator())
    if type(pool_size) == type(real_decorator):
        return real_decorator(pool_size)

    return real_decorator


def with_settings(**kw_settings):
    """
    Decorator equivalent of ``fabric.context_managers.settings``.

    Allows you to wrap an entire function as if it was called inside a block
    with the ``settings`` context manager. This may be useful if you know you
    want a given setting applied to an entire function body, or wish to
    retrofit old code without indenting everything.

    For example, to turn aborts into warnings for an entire task function::

        @with_settings(warn_only=True)
        def foo():
            ...

    .. seealso:: `~fabric.context_managers.settings`
    .. versionadded:: 1.1
    """
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            with settings(**kw_settings):
                return func(*args, **kwargs)
        return _wrap_as_new(func, inner)
    return outer
