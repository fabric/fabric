"""
Convenience decorators for use in fabfiles.
"""
from __future__ import with_statement

from functools import wraps

# from Crypto import Random
from .context_managers import settings


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

    As with `~swatch.decorators.hosts`, `~swatch.decorators.roles` may be
    invoked with either an argument list or a single, iterable argument.
    Similarly, this decorator uses the same mechanism as
    `~swatch.decorators.hosts` and simply sets ``<function>.roles``.

    .. versionchanged:: 0.9.2
        Allow a single, iterable argument to be used (same as
        `~swatch.decorators.hosts`).
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

    .. note:: ``runs_once`` does not work with parallel task execution.
    """

    @wraps(func)
    def decorated(*args, **kwargs):
        if not hasattr(decorated, 'return_value'):
            decorated.return_value = func(*args, **kwargs)
        return decorated.return_value

    decorated = _wrap_as_new(func, decorated)
    # Mark as serial (disables parallelism) and return
    return serial(decorated)


def with_settings(*arg_settings, **kw_settings):
    """
    Decorator equivalent of ``swatch.context_managers.settings``.

    Allows you to wrap an entire function as if it was called inside a block
    with the ``settings`` context manager. This may be useful if you know you
    want a given setting applied to an entire function body, or wish to
    retrofit old code without indenting everything.

    For example, to turn aborts into warnings for an entire task function::

        @with_settings(warn_only=True)
        def foo():
            ...

    .. seealso:: `~swatch.context_managers.settings`
    .. versionadded:: 1.1
    """

    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            with settings(*arg_settings, **kw_settings):
                return func(*args, **kwargs)

        return _wrap_as_new(func, inner)

    return outer
