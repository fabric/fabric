"""
Internal subroutines for e.g. aborting execution with an error message,
or handling Fabric-specific string formatting.
"""

import re
import sys

from state import env


FORMAT_REGEX = re.compile(r'(\\?)(\$\((?P<var>[\w-]+?)\))')

def format(s):
    """
    Replace "$(foo)" style references to ENV vars in given string, and return
    the result.
    """
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
    """
    print("Error: " + format(msg))
    sys.exit(1)


def warn(msg):
    """
    Print warning message, but do not abort execution.
    """
    print("Warning: " + format(msg))
