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


def indent(text, spaces=4, strip=False):
    """
    Returns text indented by the given number of spaces.

    If text is not a string, it is assumed to be a list of lines and will be
    joined by ``\\n`` prior to indenting.

    When ``strip`` is ``True``, a minimum amount of whitespace is removed from
    the left-hand side of the given string (so that relative indents are
    preserved, but otherwise things are left-stripped). This allows you to
    effectively "normalize" any previous indentation for some inputs.
    """
    # Normalize strings into lists of lines
    if hasattr(text, 'splitlines'):
        lines = text.splitlines()
    else:
        lines = text
    if strip:
        # Find shortest amount of left-facing whitespace
        shortest = max([len(x) for x in lines])
        for line in filter(None, lines):
            whitespace = shortest
            for index, character in enumerate(line):
                if not character.isspace():
                    whitespace = index
                    break
            if whitespace < shortest:
                shortest = whitespace
        # Cut off that amount from each string in the line (i.e. unindent)
        lines = [x[whitespace:] for x in lines]
    prefix = ' ' * spaces
    # Join lines and indent
    output = '\n'.join(prefix + line for line in lines)
    # Strip out empty lines before/aft
    output = output.strip()
    # Reintroduce first indent (which just got stripped out)
    output = prefix + output
    return output
