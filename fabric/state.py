"""
Internal shared-state variables such as config settings and host lists.
"""

import re
import socket
import sys
from optparse import make_option

from fabric.utils import abort, get_system_username
from fabric.network import HostConnectionCache


#
# Paramiko
#

try:
    import paramiko as ssh
except ImportError:
    abort("paramiko is a required module. Please install it:\n\t$ sudo easy_install paramiko")


#
# Win32 flag
#

# Impacts a handful of platform specific behaviors.
win32 = sys.platform in ['win32', 'cygwin']


#
# Environment dictionary
# 

class _AttributeDict(dict):
    """
    Dictionary subclass enabling attribute lookup/assignment of keys/values.

    For example::

        >>> m = _AttributeDict({'foo': 'bar'})
        >>> m.foo
        bar
        >>> m.foo = 'not bar'
        >>> m['foo']
        not bar

    ``_AttributeDict`` objects also provide ``.first()`` which acts like
    ``.get()`` but accepts multiple keys as arguments, and returns the value of
    the first hit, e.g.::

        >>> m = _AttributeDict({'foo': 'bar', 'biz': 'baz'})
        >>> m.first('wrong', 'incorrect', 'foo', 'biz')
        bar

    """
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def first(self, *names):
        for name in names:
            value = self.get(name)
            if value:
                return value

# Options/settings which exist both as environment keys and which can be set
# on the command line, are defined here. When used via `fab` they will be added
# to the optparse parser, and either way they are added to `env` below (i.e.
# the 'dest' value becomes the environment key and the value, the env value).
#
# Keep in mind that optparse changes hyphens to underscores when automatically
# deriving the `dest` name, e.g. `--reject-unknown-keys` becomes
# `reject_unknown_keys`.
#
# Furthermore, *always* specify some sort of default to avoid ending up with
# optparse.NO_DEFAULT (currently a two-tuple)! None is better than ''.
env_options = [

    # By default, we accept unknown host keys. This option allows users to
    # disable that behavior (which means Fabric will raise an exception and
    # terminate when an unknown host key is received from a server).
    make_option('-R', '--reject-unknown-keys',
        action='store_true',
        default=False,
        help="reject unknown host keys"
    ),

    # Password
    make_option('-p', '--password',
        default=None,
        help='password for use with authentication and/or sudo'
    ),

    # Private key file
    make_option('-i', 
        action='append',
        dest='key_filename',
        default=None,
        help='path to SSH private key file. May be repeated.'
    )


    # TODO: verbosity selection (sets state var(s) used when printing)
    # Could default to typical -v/--verbose disabling fab_quiet; or could do
    # multiple levels, e.g. -vvv, OR could specifically enable/disable stuff,
    # e.g. --no-warnings / --no-echo (no echoing commands) / --no-stdout / etc.

]

# Global environment dict. Currently a catchall for everything: config settings
# such as global deep/broad mode, host lists, username etc.
# Most default values are specified in `env_options` above, in the interests of
# preserving DRY.
env = _AttributeDict({
    # Version number for --version
    'version': '0.2.0',
    # Filename of Fab settings file
    'settings_file': '.fabricrc',
    # Flag for whether we're running via the `fab` command (determines some
    # behavioral changes such as using sys.exit() or not)
    'invoked_as_fab': False
})

# Add in option defaults
for option in env_options:
    env[option.dest] = option.default

# System username (done here for library use)
env.system_username = get_system_username()


#
# Command dictionary
#

# Keys are the command/function names, values are the callables themselves.
# This is filled in when main() runs.
commands = {}


#
# Host connection dict/cache
#

connections = HostConnectionCache()
