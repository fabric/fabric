"""
Convenience decorators for use in fabfiles.
"""


def hosts(*host_list):
    """
    Decorator attaching its arg list to the wrapped function as ``.hosts``.

    For example::

        @hosts('a', 'b', 'c')
        def my_func():
            pass

    Once its module is loaded, ``my_func`` will exhibit a ``.hosts`` attribute
    equal to ``['a', 'b', 'c']``.
    """
    def attach_hosts(func):
        @wraps(func)
        def inner_decorator(*args, **kwargs):
            return func(*args, **kwargs)
        inner_decorator.hosts = host_list
        return inner_decorator
    return attach_hosts


def runs_once(func):
    """
    Decorator preventing wrapped function from running more than once.

    By keeping internal state, this decorator allows you to mark a function
    such that it will only run once per Python interpreter session, which in
    typical use means "once per invocation of the ``fab`` program".

    Any function wrapped with this decorator will silently fail to execute the
    2nd, 3rd, ..., Nth time it is called, and will return None in that instance.
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        if hasattr(decorated, 'has_run'):
            return
        else:
            decorated.has_run = True
            return func(*args, **kwargs)
    return decorated
