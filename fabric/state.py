"""
Internal shared-state variables such as config settings and host lists.
"""

import os
import sys
from optparse import make_option

from fabric.network import HostConnectionCache
from fabric.version import get_version


#
# Win32 flag
#

# Impacts a handful of platform specific behaviors. Note that Cygwin's Python
# is actually close enough to "real" UNIXes that it doesn't need (or want!) to
# use PyWin32 -- so we only test for literal Win32 setups (vanilla Python,
# ActiveState etc) here.
win32 = (sys.platform == 'win32')


#
# Environment dictionary - support structures
#

class _AttributeDict(dict):
    """
    Dictionary subclass enabling attribute lookup/assignment of keys/values.

    For example::

        >>> m = _AttributeDict({'foo': 'bar'})
        >>> m.foo
        'bar'
        >>> m.foo = 'not bar'
        >>> m['foo']
        'not bar'

    ``_AttributeDict`` objects also provide ``.first()`` which acts like
    ``.get()`` but accepts multiple keys as arguments, and returns the value of
    the first hit, e.g.::

        >>> m = _AttributeDict({'foo': 'bar', 'biz': 'baz'})
        >>> m.first('wrong', 'incorrect', 'foo', 'biz')
        'bar'

    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

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
        try:
            username = pwd.getpwuid(os.getuid())[0]
        # getpwuid raises KeyError if it cannot find a username for the given
        # UID, e.g. on ep.io and similar "non VPS" style services. Rather than
        # error out, just set the 'default' username to None. Can check for
        # this value later if required.
        except KeyError:
            username = None
        return username
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
            SHGetSpecialFolderPath(0, CSIDL_PROFILE),
            rc_file
        )


# Options/settings which exist both as environment keys and which can be set on
# the command line, are defined here. When used via `fab` they will be added to
# the optparse parser, and either way they are added to `env` below (i.e.  the
# 'dest' value becomes the environment key and the value, the env value).
#
# Keep in mind that optparse changes hyphens to underscores when automatically
# deriving the `dest` name, e.g. `--reject-unknown-hosts` becomes
# `reject_unknown_hosts`.
#
# Furthermore, *always* specify some sort of default to avoid ending up with
# optparse.NO_DEFAULT (currently a two-tuple)! In general, None is a better
# default than ''.
#
# User-facing documentation for these are kept in docs/env.rst.
env_options = [

    make_option('-r', '--reject-unknown-hosts',
        action='store_true',
        default=False,
        help="reject unknown hosts"
    ),

    make_option('-D', '--disable-known-hosts',
        action='store_true',
        default=False,
        help="do not load user known_hosts file"
    ),

    make_option('-u', '--user',
        default=_get_system_username(),
        help="username to use when connecting to remote hosts"
    ),

    make_option('-p', '--password',
        default=None,
        help="password for use with authentication and/or sudo"
    ),

    make_option('-H', '--hosts',
        default=[],
        help="comma-separated list of hosts to operate on"
    ),

    make_option('-R', '--roles',
        default=[],
        help="comma-separated list of roles to operate on"
    ),

    make_option('-x', '--exclude-hosts',
        default=[],
        help="comma-separated list of hosts to exclude"
    ),

    make_option('-i', 
        action='append',
        dest='key_filename',
        default=None,
        help="path to SSH private key file. May be repeated."
    ),

    # Use -a here to mirror ssh(1) options.
    make_option('-a', '--no_agent',
        action='store_true',
        default=False,
        help="don't use the running SSH agent"
    ),

    # No matching option for ssh(1) so just picked something appropriate.
    make_option('-k', '--no-keys',
        action='store_true',
        default=False,
        help="don't load private key files from ~/.ssh/"
    ),

    make_option('-f', '--fabfile',
        default='fabfile',
        help="Python module file to import, e.g. '../other.py'"
    ),

    make_option('-w', '--warn-only',
        action='store_true',
        default=False,
        help="warn, instead of abort, when commands fail"
    ),

    make_option('-s', '--shell',
        default='/bin/bash -l -c',
        help="specify a new shell, defaults to '/bin/bash -l -c'"
    ),

    make_option('-c', '--config',
        dest='rcfile',
        default=_rc_path(),
        help="specify location of config file to use"
    ),

    # Verbosity controls, analogous to context_managers.(hide|show)
    make_option('--hide',
        metavar='LEVELS',
        help="comma-separated list of output levels to hide"
    ),
    make_option('--show',
        metavar='LEVELS',
        help="comma-separated list of output levels to show"
    ),

    # Global PTY flag for run/sudo
    make_option('--no-pty',
        dest='always_use_pty',
        action='store_false',
        default=True,
        help="do not use pseudo-terminal in run/sudo"
    ),

    # Abort on prompting flag
    make_option('--abort-on-prompts',
        action='store_true',
        default=False,
        help="Abort instead of prompting (for password, host, etc)"
    ),

    # Keepalive
    make_option('--keepalive',
        dest='keepalive',
        type=int,
        default=0,
        help="enables a keepalive every n seconds"
    ),
]


#
# Environment dictionary - actual dictionary object
#


# Global environment dict. Currently a catchall for everything: config settings
# such as global deep/broad mode, host lists, username etc.
# Most default values are specified in `env_options` above, in the interests of
# preserving DRY: anything in here is generally not settable via the command
# line.
env = _AttributeDict({
    'again_prompt': 'Sorry, try again.',
    'all_hosts': [],
    'combine_stderr': True,
    'command': None,
    'command_prefixes': [],
    'cwd': '',  # Must be empty string, not None, for concatenation purposes
    'echo_stdin': True,
    'exclude_hosts': [],
    'host': None,
    'host_string': None,
    'lcwd': '',  # Must be empty string, not None, for concatenation purposes
    'local_user': _get_system_username(),
    'output_prefix': True,
    'passwords': {},
    'path': '',
    'path_behavior': 'append',
    'port': None,
    'real_fabfile': None,
    'roles': [],
    'roledefs': {},
    # -S so sudo accepts passwd via stdin, -p with our known-value prompt for
    # later detection (thus %s -- gets filled with env.sudo_prompt at runtime)
    'sudo_prefix': "sudo -S -p '%s' ",
    'sudo_prompt': 'sudo password:',
    'use_shell': True,
    'user': None,
    'version': get_version('short')
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


def default_channel():
    """
    Return a channel object based on ``env.host_string``.
    """
    chan = connections[env.host_string].get_transport().open_session()
    chan.input_enabled = True
    return chan


#
# Output controls
#

class _AliasDict(_AttributeDict):
    """
    `_AttributeDict` subclass that allows for "aliasing" of keys to other keys.

    Upon creation, takes an ``aliases`` mapping, which should map alias names
    to lists of key names. Aliases do not store their own value, but instead
    set (override) all mapped keys' values. For example, in the following
    `_AliasDict`, calling ``mydict['foo'] = True`` will set the values of
    ``mydict['bar']``, ``mydict['biz']`` and ``mydict['baz']`` all to True::

        mydict = _AliasDict(
            {'biz': True, 'baz': False},
            aliases={'foo': ['bar', 'biz', 'baz']}
        )

    Because it is possible for the aliased values to be in a heterogenous
    state, reading aliases is not supported -- only writing to them is allowed.
    This also means they will not show up in e.g. ``dict.keys()``.

    ..note::

        Aliases are recursive, so you may refer to an alias within the key list
        of another alias. Naturally, this means that you can end up with
        infinite loops if you're not careful.

    `_AliasDict` provides a special function, `expand_aliases`, which will take
    a list of keys as an argument and will return that list of keys with any
    aliases expanded. This function will **not** dedupe, so any aliases which
    overlap will result in duplicate keys in the resulting list.
    """
    def __init__(self, arg=None, aliases=None):
        init = super(_AliasDict, self).__init__
        if arg is not None:
            init(arg)
        else:
            init()
        # Can't use super() here because of _AttributeDict's setattr override
        dict.__setattr__(self, 'aliases', aliases)

    def __setitem__(self, key, value):
        if key in self.aliases:
            for aliased in self.aliases[key]:
                self[aliased] = value
        else:
            return super(_AliasDict, self).__setitem__(key, value)

    def expand_aliases(self, keys):
        ret = []
        for key in keys:
            if key in self.aliases:
                ret.extend(self.expand_aliases(self.aliases[key]))
            else:
                ret.append(key)
        return ret


# Keys are "levels" or "groups" of output, values are always boolean,
# determining whether output falling into the given group is printed or not
# printed.
#
# By default, everything except 'debug' is printed, as this is what the average
# user, and new users, are most likely to expect.
#
# See docs/usage.rst for details on what these levels mean.
output = _AliasDict({
    'status': True,
    'aborts': True,
    'warnings': True,
    'running': True,
    'stdout': True,
    'stderr': True,
    'debug': False,
    'user': True
}, aliases={
    'everything': ['warnings', 'running', 'user', 'output'],
    'output': ['stdout', 'stderr']
})


#
# I/O loop sleep parameter (in seconds)
#

io_sleep = 0.01
