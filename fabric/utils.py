"""
Internal subroutines for e.g. aborting execution with an error message,
or performing indenting on multiline output.

As this file's contents are used by the ``state`` module, all uses of ``state``
must be imported within each function and not at the module level.
"""

from functools import wraps
import os
import sys


def abort(msg):
    """
    Abort execution, printing given message and exiting with error status.
    When not invoked as the ``fab`` command line tool, raise an exception
    instead.
    """
    print >>sys.stderr, "\nError: " + msg
    sys.exit(1)

    
def warn(msg):
    """
    Print warning message, but do not abort execution.
    """
    print >>sys.stderr, "Warning: " + msg


def indent(text, spaces=4):
    """
    Returns text indented by the given number of spaces.

    If text is not a string, it is assumed to be a list of lines and will be
    joined by ``\n`` prior to indenting.
    """
    if not hasattr(text, 'splitlines'):
        text = '\n'.join(text)
    return '\n'.join(((' ' * spaces) + line for line in text.splitlines()))


def get_system_username():
    """
    Obtain name of current system user, which will be default connection user.
    """
    from state import win32
    if not win32:
        import pwd
        return pwd.getpwuid(os.getuid())[0]
    else:
        import win32api
        import win32security
        import win32profile
        return win32api.GetUserName()


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


def escape_quotes(string):
    return string.replace('"', r'\"')
