"""
Internal shared-state variables such as config settings and host lists.
"""

import re
import sys
from optparse import make_option

from utils import abort

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

    For example:

        >>> m = _AttributeDict({'foo': 'bar'})
        >>> m.foo
        bar
        >>> m.foo = 'not bar'
        >>> m['foo']
        not bar

    _AttributeDict objects also provide .first() which acts like .get() but
    accepts multiple keys as arguments, and returns the value of the first hit,
    e.g.

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
env_options = [

    # By default, we accept unknown host keys. This option allows users to
    # disable that behavior (which means Fabric will raise an exception and
    # terminate when an unknown host key is received from a server).
    make_option('-R', '--reject-unknown-keys',
        action='store_true',
        default=False,
        help="reject unknown host keys"
    ),

    # TODO: verbosity selection (sets state var(s) used when printing)
    # Could default to typical -v/--verbose disabling fab_quiet; or could do
    # multiple levels, e.g. -vvv, OR could specifically enable/disable stuff,
    # e.g. --no-warnings / --no-echo (no echoing commands) / --no-stdout / etc.

]

# Global environment dict. Currently a catchall for everything: config settings
# such as global deep/broad mode, host lists, username etc.
env = _AttributeDict({
    'version': '0.2.0',
    'settings_file': '.fabricrc',
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
# Host connection cache
#

class _HostConnectionCache(dict):
    """
    Dict subclass allowing for caching of host connections/clients.

    This subclass does not offer any extra methods, but will intelligently
    create new client connections when keys are requested, or return previously
    created connections instead.

    Key values are the same as host specifiers throughout Fabric: optional
    username + '@', mandatory hostname, optional ':' + port number. Examples:

    * 'example.com' - typical Internet host address
    * 'firewall' - atypical, but still legal, local host address
    * 'user@example.com' - with specific username attached.

    When the username is not given, `env.username` is used; if `env.username`
    is not defined, the local system username is assumed.

    Note that differing explicit usernames for the same hostname will
    result in multiple client connections being made. For example, specifying
    'user1@example.com' will create a new connection to 'example.com', logged
    in as 'user1'; later specifying 'user2@example.com' will create a new, 2nd
    connection as 'user2'.
    
    The same applies to ports: specifying two different ports will result in
    two different connections to the same host being made. If no port is given,
    22 is assumed, so 'example.com' is equivalent to 'example.com:22'.
    """
    host_pattern = r'((?P<user>\w+)@)?(?P<hostname>[\w.]+)(:(?P<port>\d+))?'
    host_regex = re.compile(host_pattern)

    def __getitem__(self, key):
        # Get user, hostname and port separately
        r = self.host_regex.match(key).groupdict()
        # Add any necessary defaults in
        user = r['user'] or env.get('username') or env.system_username
        hostname = r['hostname']
        port = r['port'] or '22'
        # Put them back together for the "real" key
        real_key = "%s@%s:%s" % (user, hostname, port)
        # If not found, create new connection and store it
        if real_key not in self:
            self[real_key] = self._connect(user, hostname, port)
        # Return the value either way
        return dict.__getitem__(self, real_key)

    @staticmethod
    def _connect(user, hostname, port):
        """
        Static helper method which generates a new SSH connection.
        """
        return None
