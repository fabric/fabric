"""
Internal subroutines for e.g. aborting execution with an error message,
or performing indenting on multiline output.
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
