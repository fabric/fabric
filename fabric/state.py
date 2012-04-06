"""
Internal shared-state variables such as config settings and host lists.
"""

import os
import sys
from optparse import make_option

from fabric.network import HostConnectionCache
from fabric.version import get_version
from fabric.utils import _AliasDict, _AttributeDict


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

default_port = '22' # hurr durr
default_ssh_config_path = '~/.ssh/config'

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

    make_option('-a', '--no_agent',
        action='store_true',
        default=False,
        help="don't use the running SSH agent"
    ),

    make_option('-A', '--forward-agent',
        action='store_true',
        default=False,
        help="forward local agent to remote end"
    ),

    make_option('--abort-on-prompts',
        action='store_true',
        default=False,
        help="abort instead of prompting (for password, host, etc)"
    ),

    make_option('-c', '--config',
        dest='rcfile',
        default=_rc_path(),
        metavar='PATH',
        help="specify location of config file to use"
    ),

    make_option('-D', '--disable-known-hosts',
        action='store_true',
        default=False,
        help="do not load user known_hosts file"
    ),

    make_option('-f', '--fabfile',
        default='fabfile',
        metavar='PATH',
        help="python module file to import, e.g. '../other.py'"
    ),

    make_option('--hide',
        metavar='LEVELS',
        help="comma-separated list of output levels to hide"
    ),

    make_option('-H', '--hosts',
        default=[],
        help="comma-separated list of hosts to operate on"
    ),

    make_option('-i', 
        action='append',
        dest='key_filename',
        metavar='PATH',
        default=None,
        help="path to SSH private key file. May be repeated."
    ),

    make_option('-k', '--no-keys',
        action='store_true',
        default=False,
        help="don't load private key files from ~/.ssh/"
    ),

    make_option('--keepalive',
        dest='keepalive',
        type=int,
        default=0,
        metavar="N",
        help="enables a keepalive every N seconds"
    ),

    make_option('--linewise',
        action='store_true',
        default=False,
        help="print line-by-line instead of byte-by-byte"
    ),

    make_option('-n', '--connection-attempts',
        type='int',
        metavar='M',
        dest='connection_attempts',
        default=1,
        help="make M attempts to connect before giving up"
    ),

    make_option('--no-pty',
        dest='always_use_pty',
        action='store_false',
        default=True,
        help="do not use pseudo-terminal in run/sudo"
    ),

    make_option('-p', '--password',
        default=None,
        help="password for use with authentication and/or sudo"
    ),

    make_option('-P', '--parallel',
        dest='parallel',
        action='store_true',
        default=False,
        help="default to parallel execution method"
    ),

    make_option('--port',
        default=default_port,
        help="SSH connection port"
    ),

    make_option('-r', '--reject-unknown-hosts',
        action='store_true',
        default=False,
        help="reject unknown hosts"
    ),

    make_option('-R', '--roles',
        default=[],
        help="comma-separated list of roles to operate on"
    ),

    make_option('-s', '--shell',
        default='/bin/bash -l -c',
        help="specify a new shell, defaults to '/bin/bash -l -c'"
    ),

    make_option('--show',
        metavar='LEVELS',
        help="comma-separated list of output levels to show"
    ),

    make_option('--skip-bad-hosts',
        action="store_true",
        default=False,
        help="skip over hosts that can't be reached"
    ),

    make_option('--ssh-config-path',
        default=default_ssh_config_path,
        metavar='PATH',
        help="Path to SSH config file"
    ),

    make_option('-t', '--timeout',
        type='int',
        default=10,
        metavar="N",
        help="set connection timeout to N seconds"
    ),

    make_option('-u', '--user',
        default=_get_system_username(),
        help="username to use when connecting to remote hosts"
    ),

    make_option('-w', '--warn-only',
        action='store_true',
        default=False,
        help="warn, instead of abort, when commands fail"
    ),

    make_option('-x', '--exclude-hosts',
        default=[],
        metavar='HOSTS',
        help="comma-separated list of hosts to exclude"
    ),

    make_option('-z', '--pool-size',
            dest='pool_size',
            type='int',
            metavar='INT',
            default=0,
            help="number of concurrent processes to use in parallel mode",
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
    'default_port': default_port,
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
    'port': default_port,
    'real_fabfile': None,
    'roles': [],
    'roledefs': {},
    'skip_bad_hosts': False,
    'ssh_config_path': default_ssh_config_path,
    # -S so sudo accepts passwd via stdin, -p with our known-value prompt for
    # later detection (thus %s -- gets filled with env.sudo_prompt at runtime)
    'sudo_prefix': "sudo -S -p '%(sudo_prompt)s' ",
    'sudo_prompt': 'sudo password:',
    'use_exceptions_for': {'network': False},
    'use_shell': True,
    'use_ssh_config': False,
    'user': None,
    'version': get_version('short')
})

# Fill in exceptions settings
exceptions = ['network']
exception_dict = {}
for e in exceptions:
    exception_dict[e] = False
env.use_exceptions_for = _AliasDict(exception_dict,
    aliases={'everything': exceptions})


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
    'output': ['stdout', 'stderr'],
    'commands': ['stdout', 'running']
})
