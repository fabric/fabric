"""
Internal subroutines for e.g. aborting execution with an error message,
or handling Fabric-specific string formatting.

As this file's contents are used by the `state` module, all uses of `state` must
be imported within each function and not at the module level.
"""

import os
import re
import sys


FORMAT_REGEX = re.compile(r'(\\?)(\$\((?P<var>[\w-]+?)\))')

def format(s):
    """
    Replace "$(foo)" style references to env vars in given string, and return
    the result.
    """
    from state import env
    if s is None:
        return None
    # Escape percent signs
    s = s.replace('%', '%%')
    # Function to go from match object => new string
    def func(match):
        escape = match.group(1)
        if escape == '\\':
            return match.group(2)
        var = match.group('var')
        if var in env:
            return escape + format(str(env[var]) % env)
        else:
            return match.group(0)
    return re.sub(FORMAT_REGEX, func, s % env)


def abort(msg):
    """
    Abort execution, printing given message and exiting with error status.
    When not invoked as the `fab` command line tool, raise an exception instead.
    """
    from state import env
    if env.invoked_as_fab:
        print("\nError: " + format(msg))
        sys.exit(1)
    # TODO: Make our own exception, or figure out if a more specific builtin
    # exception applies here.
    raise StandardError


def warn(msg):
    """
    Print warning message, but do not abort execution.
    """
    print("Warning: " + format(msg))


def indent(text, spaces=4):
    """
    Returns text indented by the given number of spaces.

    If text is not a string, it is assumed to be a list of lines and will be
    joined by \n prior to indenting.
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
