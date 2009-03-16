"""
Package-level constructs. Currently, the only code not in sub-modules is the below version-related constant/method.
"""

VERSION = (0, 2, 0, 'alpha', 0)

# Version code inspired by Django
def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        version = '%s %s' % (version, VERSION[3])
        if VERSION[3] != 'final':
            version = '%s %s' % (version, VERSION[4])
    return version

__version__ = get_version()
