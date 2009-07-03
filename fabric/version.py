"""
Current Fabric version constant plus version pretty-print method.

This functionality is contained in its own module to prevent circular import
problems with ``__init__.py`` (which is loaded by setup.py during installation,
which in turn needs access to this version information.)
"""

VERSION = (1, 0, 0, 'alpha', 0)

def get_version(verbose=False, line_only=False):
    """
    Return a version string for this package, based on `VERSION`.

    When ``verbose`` is False (the default), `get_version` prints a
    tag-friendly version of the string, e.g. '0.9a2'.

    When ``verbose`` is True, a slightly more human-readable version is
    produced, e.g. '0.9 alpha 2'.

    When ``line_only`` is True, only the major and minor version numbers are
    returned, e.g. '0.9'.

    This code is based off of Django's similar version output algorithm.
    """
    # Major + minor only
    version = '%s.%s' % (VERSION[0], VERSION[1])
    # Break off now if we only want the line of development
    if line_only:
        return version
    # Append tertiary/patch if non-zero
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    # Append alpha/beta modifier if not a final release
    if VERSION[3] != 'final':
        # If non-verbose, just the first letter of the modifier, and no spaces.
        if not verbose:
            version = '%s%s%s' % (version, VERSION[3][0], VERSION[4])
        # Otherwise, be more generous.
        else:
            version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    # If it is final, and we're being verbose, also tack on the 'final'.
    elif verbose:
        version = '%s %s' % (version, VERSION[3])

    return version

__version__ = get_version()
