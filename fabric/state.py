"""
Internal shared-state variables such as config settings and host lists.
"""

import re
import socket
import sys
from optparse import make_option

from utils import abort, get_system_username


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
    host_pattern = r'((?P<username>\w+)@)?(?P<hostname>[\w.]+)(:(?P<port>\d+))?'
    host_regex = re.compile(host_pattern)

    def __getitem__(self, key):
        real_key = self.normalize(key)
        # If not found, create new connection and store it
        if real_key not in self:
            self[real_key] = self.connect(username, hostname, port)
        # Return the value either way
        return dict.__getitem__(self, real_key)

    @classmethod
    def normalize(self, host_string):
        """
        Normalizes or fleshes out a host string to its full user@host:port form.
        """
        # Get user, hostname and port separately
        r = self.host_regex.match(host_string).groupdict()
        # Add any necessary defaults in
        username = r['username'] or env.get('username') or env.system_username
        hostname = r['hostname']
        port = r['port'] or '22'
        # Put them back together for fully normalized result.
        return "%s@%s:%s" % (username, hostname, port)

    @staticmethod
    def connect(username, hostname, port):
        """
        Static helper method which generates a new SSH connection.
        """
        #
        # Initialization
        #

        # Init client
        client = ssh.SSHClient()
        # Load known host keys (e.g. ~/.ssh/known_hosts)
        client.load_system_host_keys()
        # Unless user specified not to, accept/add new, unknown host keys
        if not env.reject_unknown_keys:
            client.set_missing_host_key_policy(ssh.AutoAddPolicy())

        #
        # Connection attempt loop
        #

        # Initialize loop variables
        connected = False
        bad_password = False
        suffix = '' # Defined here so it persists across loop iterations
        password = env.password

        # Loop until successful connect (keep prompting for new password)
        while not connected:
            # Attempt connection
            try:
                client.connect(hostname, int(port), username, password,
                    key_filename=env.key_filename, timeout=10)
                connected = True
                return client
            # Prompt for new password to try on auth failure
            except (ssh.AuthenticationException, ssh.SSHException):
                # Unless this is the first time we're here, tell user the
                # supplied password was bogus.
                if bad_password:
                    # Reprimand user
                    print("Bad password.")
                    # Reset prompt suffix
                    suffix = ": "
                # If not, do we have one to try?
                elif password:
                    # Imply we'll reuse last one entered, in prompt
                    suffix = " [Enter for previous]: "
                # Otherwise, use default prompt suffix
                else:
                    suffix = ": "
                # Whatever password we tried last time was bad, so take note
                bad_password = True
                # Update current password with user input (loop will try again)
                password = getpass.getpass("Password for %s@%s%s" % (
                    username, hostname, suffix))
            # Ctrl-D / Ctrl-C for exit
            except (EOFError, TypeError):
                if env.invoked_as_fab:
                    # Print a newline (in case user was sitting at prompt)
                    print('')
                    sys.exit(0)
                raise
            # Handle timeouts
            except socket.timeout:
                abort('Error: timed out trying to connect to %s' % hostname)
            # Handle DNS error / name lookup failure
            except socket.gaierror:
                abort('Error: name lookup failed for %s' % hostname)
            # Handle generic network-related errors
            # NOTE: In 2.6, socket.error subclasses IOError
            except socket.error, e:
                abort('Low level socket error connecting to host %s: %s' % (
                    hostname, e[1])
                )

# Actual cache instance
connections = _HostConnectionCache()
