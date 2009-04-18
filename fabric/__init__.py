VERSION = (0, 9, 0, 'alpha', 0)

# Version code inspired by Django (but modified to be setuptools/PyPI ready)
def get_version():
    # Major + minor only
    version = '%s.%s' % (VERSION[0], VERSION[1])
    # Append tertiary/patch if non-zero
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    # Append alpha/beta modifier if not a final release (first char + number)
    if VERSION[3] != 'final':
        version = '%s%s%s' % (version, VERSION[3][0], VERSION[4])
    return version

__version__ = get_version()
