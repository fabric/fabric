"""
Internal shared-state variables such as config settings and host lists.
"""

import os
import re
import socket
import sys
from optparse import make_option

from fabric.utils import abort
from fabric.network import HostConnectionCache
from fabric.version import get_version


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
# Environment dictionary - support structures
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
        if key in self:
            return self[key]
        else:
            raise AttributeError # to conform with __getattr__ spec


    def __setattr__(self, key, value):
        self[key] = value

    def first(self, *names):
        for name in names:
            value = self.get(name)
            if value:
                return value


# By default, if the user (including code using Fabric as a library) doesn't
# set the username, we obtain the currently running username and use that.
def _get_system_username():
    """
    Obtain name of current system user, which will be default connection user.
    """
    if not win32:
        import pwd
        return pwd.getpwuid(os.getuid())[0]
    else:
        import win32api
        import win32security
        import win32profile
        return win32api.GetUserName()


def _rc_path():
    """
    Return platform-specific default file path for $HOME/.fabricrc.
    """
    rc_file = '.fabricrc'
    if not win32:
        return os.path.expanduser("~/" + rc_file)
    else:
        from win32com.shell.shell import SHGetSpecialFolderPath
        from win32com.shell.shellcon import CSIDL_PROFILE
        return "%s/%s" % (
            SHGetSpecialFolderPath(0,CSIDL_PROFILE),
            rc_file
        )


# Options/settings which exist both as environment keys and which can be set
# on the command line, are defined here. When used via `fab` they will be added
# to the optparse parser, and either way they are added to `env` below (i.e.
# the 'dest' value becomes the environment key and the value, the env value).
#
# Keep in mind that optparse changes hyphens to underscores when automatically
# deriving the `dest` name, e.g. `--reject-unknown-hosts` becomes
# `reject_unknown_hosts`.
#
# Furthermore, *always* specify some sort of default to avoid ending up with
# optparse.NO_DEFAULT (currently a two-tuple)! None is better than ''.
env_options = [

    # By default, we accept unknown hosts' keys. This option allows users to
    # disable that behavior (which means Fabric will raise an exception and
    # terminate when an unknown host key is received from a server).
    make_option('-r', '--reject-unknown-hosts',
        action='store_true',
        default=False,
        help="reject unknown hosts"
    ),

    # By default, we load the user's ~/.ssh/known_hosts file. In some cases
    # users may not want this to occur.
    make_option('-D', '--disable-known-hosts',
        action='store_true',
        default=False,
        help="do not load user known_hosts file"
    ),

    # Username
    make_option('-u', '--user',
        default=_get_system_username(),
        help="username to use when connecting to remote hosts"
    ),

    # Password
    make_option('-p', '--password',
        default=None,
        help="password for use with authentication and/or sudo"
    ),

    # Global host list
    make_option('-H', '--hosts',
        default=None,
        help="comma-separated list of hosts to operate on"
    ),

    # Global role list
    make_option('-R', '--roles',
        default=None,
        help="comma-separated list of roles to operate on"
    ),

    # Private key file
    make_option('-i', 
        action='append',
        dest='key_filename',
        default=None,
        help="path to SSH private key file. May be repeated."
    ),

    # Fabfile name to look for
    make_option('-f', '--fabfile',
        default='fabfile.py',
        help="name of fabfile to load, e.g. 'fabfile.py' or '../other.py'"
    ),

    # Default error-handling behavior
    make_option('-w', '--warn-only',
        action='store_true',
        default=False,
        help="warn, instead of abort, when commands fail"
    ),

    # Shell used when running remote commands
    make_option('-s', '--shell',
        default='/bin/bash -l -c',
        help="specify a new shell, defaults to '/bin/bash -l -c'"
    ),

    # Debug output
    # TODO: tie into global output controls better (this is just a stopgap)
    make_option('--debug',
        action='store_true',
        default=False,
        help="display debug output"
    ),

    # Config file location
    make_option('-c', '--config',
        dest='rcfile',
        default=_rc_path(),
        help="specify location of config file to use"
    )


    # TODO: verbosity selection (sets state var(s) used when printing)
    # Could default to typical -v/--verbose disabling fab_quiet; or could do
    # multiple levels, e.g. -vvv, OR could specifically enable/disable stuff,
    # e.g. --no-warnings / --no-echo (no echoing commands) / --no-stdout / etc.
    
]


#
# Environment dictionary - actual dictionary object
#


# Global environment dict. Currently a catchall for everything: config settings
# such as global deep/broad mode, host lists, username etc.
# Most default values are specified in `env_options` above, in the interests of
# preserving DRY.
env = _AttributeDict({
    # Version number for --version
    'version': get_version(),
    'sudo_prompt': 'sudo password:',
    'use_shell': True,
    'roledefs': {}
})

# Add in option defaults
for option in env_options:
    env[option.dest] = option.default


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


#
# Output controls
#

# Uses _AttributeDict for ease of use; keys are "levels" or "groups" of output,
# values are always boolean, determining whether output falling into the given
# group is printed or not printed.
#
# By default, everything except 'debug' is printed, as this is what the average
# user, and new users, are most likely to expect.
output = _AttributeDict({
    # Status messages, i.e. noting when Fabric is done running, if the user
    # used a keyboard interrupt, or when servers are disconnected from.
    # These are almost always of interest to CLI users regardless.
    'status': True,
    # Abort messages. Like status messages, these should really only be turned
    # off when using Fabric as a library, and possibly not even then.
    'aborts': True,
    # Warning messages. These should usually stay on but are often useful to
    # disable when e.g. using empty "grep" output to determine some sort of
    # status.
    'warnings': True,
    # Printouts of commands being executed or files transferred, i.e.
    # "[myserver] run: ls /var/www". This group and "stdout"/"stderr" are
    # typically set to the same value, but may be toggled if the need arises.
    'running': True,
    # Local, or remote, stdout, i.e. non-error output from commands.
    'stdout': True,
    # Local, or remote, stderr, i.e. error-related output from commands.
    'stderr': True,
    # Turn on debugging. Typically off; used to see e.g. the "full" commands
    # being run (i.e. env.shell + command => '/bin/bash -l -c "ls /var/www"',
    # as well as various other debuggy-type things. May add additional output,
    # or modify pre-existing output.
    #
    # Where modifying other pieces of output (such as above example where it
    # modifies the 'running' line to show the shell and any escape characters),
    # this setting takes precedence over the other; so if "running" is False
    # but "debug" is True, you will still be shown the 'what is running' line
    # in its debugging form.
    'debug': False
})
