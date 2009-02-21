"""
Internal subroutines for e.g. aborting execution with an error message,
or handling Fabric-specific string formatting.
"""

import os
import re
import sys

from state import env, win32


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


def rc_path():
    """
    Return platform-specific file path for $HOME/<env.settings_file>.
    """
    if not win32:
        return os.path.expanduser("~/" + env.settings_file)
    else:
        from win32com.shell.shell import SHGetSpecialFolderPath
        from win32com.shell.shellcon import CSIDL_PROFILE
        return "%s/%s" % (
            SHGetSpecialFolderPath(0,CSIDL_PROFILE),
            env.settings_file
        )


def load_settings(path):
    """
    Take given file path and apply any key=value pairs to the environment dict.

    Returns True if file exists and data was added (implicit None otherwise).
    """
    if os.path.exists(path):
        comments = lambda s: s and not s.startswith("#")
        settings = filter(comments, open(path, 'r'))
        settings = [(k.strip(), v.strip()) for k, _, v in
            [s.partition('=') for s in settings]]
        if settings:
            env.update(settings)
            return True



def find_fabfile():
    """
    Attempt to locate a fabfile in current or parent directories.

    Fabfiles are defined as files named 'fabfile.py' or 'Fabfile.py'. The '.py'
    extension is required, as fabfile loading (both by 'fab' and by fabfiles
    which need other sub-fabfiles) is done via importing, not exec.

    Order of search is lowercase filename, capitalized filename, in current
    working directory (where 'fab' was invoked) and then each parent directory
    in turn.

    Returns absolute path to first match, or None if no match found.
    """
    guesses = ['fabfile.py', 'Fabfile.py']
    path = '.'
    # Stop before falling off root of filesystem (should be platform agnostic)
    while os.path.split(os.path.abspath(path))[1]:
        found = filter(lambda x: os.path.exists(os.path.join(path, x)), guesses)
        if found:
            return os.path.abspath(os.path.join(path, found[0]))
        path = os.path.join('..', path)
