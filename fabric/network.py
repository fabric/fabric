"""
Classes and subroutines dealing with network connections and related topics.
"""

from __future__ import with_statement

from functools import wraps
import getpass
import os
import re
import threading
import time
import select
import socket
import sys

from fabric.auth import get_password, set_password
from fabric.utils import abort, handle_prompt_abort
from fabric.exceptions import NetworkError

try:
    import warnings
    warnings.simplefilter('ignore', DeprecationWarning)
    import ssh
except ImportError, e:
    import traceback
    traceback.print_exc()
    print >> sys.stderr, """
There was a problem importing our SSH library (see traceback above).
Please make sure all dependencies are installed and importable.
""".rstrip()
    sys.exit(1)


host_pattern = r'((?P<user>.+)@)?(?P<host>[^:]+)(:(?P<port>\d+))?'
host_regex = re.compile(host_pattern)


class HostConnectionCache(dict):
    """
    Dict subclass allowing for caching of host connections/clients.

    This subclass does not offer any extra methods, but will intelligently
    create new client connections when keys are requested, or return previously
    created connections instead.

    Key values are the same as host specifiers throughout Fabric: optional
    username + ``@``, mandatory hostname, optional ``:`` + port number.
    Examples:

    * ``example.com`` - typical Internet host address.
    * ``firewall`` - atypical, but still legal, local host address.
    * ``user@example.com`` - with specific username attached.
    * ``bob@smith.org:222`` - with specific nonstandard port attached.

    When the username is not given, ``env.user`` is used. ``env.user``
    defaults to the currently running user at startup but may be overwritten by
    user code or by specifying a command-line flag.

    Note that differing explicit usernames for the same hostname will result in
    multiple client connections being made. For example, specifying
    ``user1@example.com`` will create a connection to ``example.com``, logged
    in as ``user1``; later specifying ``user2@example.com`` will create a new,
    2nd connection as ``user2``.

    The same applies to ports: specifying two different ports will result in
    two different connections to the same host being made. If no port is given,
    22 is assumed, so ``example.com`` is equivalent to ``example.com:22``.
    """
    def connect(self, key):
        """
        Force a new connection to ``key`` host string.
        """
        user, host, port = normalize(key)
        key = normalize_to_string(key)
        self[key] = connect(user, host, port)

    def __getitem__(self, key):
        """
        Autoconnect + return connection object
        """
        key = normalize_to_string(key)
        if key not in self:
            self.connect(key)
        return dict.__getitem__(self, key)

    #
    # Dict overrides that normalize input keys
    #

    def __setitem__(self, key, value):
        return dict.__setitem__(self, normalize_to_string(key), value)

    def __delitem__(self, key):
        return dict.__delitem__(self, normalize_to_string(key))

    def __contains__(self, key):
        return dict.__contains__(self, normalize_to_string(key))


def ssh_config(host_string=None):
    """
    Return ssh configuration dict for current env.host_string host value.

    Memoizes the loaded SSH config file, but not the specific per-host results.

    This function performs the necessary "is SSH config enabled?" checks and
    will simply return an empty dict if not. If SSH config *is* enabled and the
    value of env.ssh_config_path is not a valid file, it will abort.

    May give an explicit host string as ``host_string``.
    """
    from fabric.state import env
    if not env.use_ssh_config:
        return {}
    if '_ssh_config' not in env:
        try:
            conf = ssh.SSHConfig()
            path = os.path.expanduser(env.ssh_config_path)
            with open(path) as fd:
                conf.parse(fd)
                env._ssh_config = conf
        except IOError, e:
            abort("Unable to load SSH config file '%s'" % path)
    host = parse_host_string(host_string or env.host_string)['host']
    return env._ssh_config.lookup(host)


def key_filenames():
    """
    Returns list of SSH key filenames for the current env.host_string.

    Takes into account ssh_config and env.key_filename, including normalization
    to a list. Also performs ``os.path.expanduser`` expansion on any key
    filenames.
    """
    from fabric.state import env
    keys = env.key_filename
    # For ease of use, coerce stringish key filename into list
    if not isinstance(env.key_filename, (list, tuple)):
        keys = [keys]
    # Strip out any empty strings (such as the default value...meh)
    keys = filter(bool, keys)
    # Honor SSH config
    # TODO: fix ssh so it correctly treats IdentityFile as a list
    conf = ssh_config()
    if 'identityfile' in conf:
        keys.append(conf['identityfile'])
    return map(os.path.expanduser, keys)


def parse_host_string(host_string):
    return host_regex.match(host_string).groupdict()


def normalize(host_string, omit_port=False):
    """
    Normalizes a given host string, returning explicit host, user, port.

    If ``omit_port`` is given and is True, only the host and user are returned.

    This function will process SSH config files if Fabric is configured to do
    so, and will use them to fill in some default values or swap in hostname
    aliases.
    """
    from fabric.state import env
    # Gracefully handle "empty" input by returning empty output
    if not host_string:
        return ('', '') if omit_port else ('', '', '')
    # Parse host string (need this early on to look up host-specific ssh_config
    # values)
    r = parse_host_string(host_string)
    host = r['host']
    # Env values (using defaults if somehow earlier defaults were replaced with
    # empty values)
    user = env.user or env.local_user
    port = env.port or env.default_port
    # SSH config data
    conf = ssh_config(host_string)
    # Only use ssh_config values if the env value appears unmodified from
    # the true defaults. If the user has tweaked them, that new value
    # takes precedence.
    if user == env.local_user and 'user' in conf:
        user = conf['user']
    if port == env.default_port and 'port' in conf:
        port = conf['port']
    # Also override host if needed
    if 'hostname' in conf:
        host = conf['hostname']
    # Merge explicit user/port values with the env/ssh_config derived ones
    # (Host is already done at this point.)
    user = r['user'] or user
    port = r['port'] or port
    if omit_port:
        return user, host
    return user, host, port


def to_dict(host_string):
    user, host, port = normalize(host_string)
    return {
        'user': user, 'host': host, 'port': port, 'host_string': host_string
    }

def from_dict(arg):
    return join_host_strings(arg['user'], arg['host'], arg['port'])


def denormalize(host_string):
    """
    Strips out default values for the given host string.

    If the user part is the default user, it is removed;
    if the port is port 22, it also is removed.
    """
    from state import env
    r = host_regex.match(host_string).groupdict()
    user = ''
    if r['user'] is not None and r['user'] != env.user:
        user = r['user'] + '@'
    port = ''
    if r['port'] is not None and r['port'] != '22':
        port = ':' + r['port']
    return user + r['host'] + port


def join_host_strings(user, host, port=None):
    """
    Turns user/host/port strings into ``user@host:port`` combined string.

    This function is not responsible for handling missing user/port strings;
    for that, see the ``normalize`` function.

    If ``port`` is omitted, the returned string will be of the form
    ``user@host``.
    """
    port_string = ''
    if port:
        port_string = ":%s" % port
    return "%s@%s%s" % (user, host, port_string)


def normalize_to_string(host_string):
    """
    normalize() returns a tuple; this returns another valid host string.
    """
    return join_host_strings(*normalize(host_string))


def connect(user, host, port):
    """
    Create and return a new SSHClient instance connected to given host.
    """
    from state import env, output

    #
    # Initialization
    #

    # Init client
    client = ssh.SSHClient()

    # Load known host keys (e.g. ~/.ssh/known_hosts) unless user says not to.
    if not env.disable_known_hosts:
        client.load_system_host_keys()
    # Unless user specified not to, accept/add new, unknown host keys
    if not env.reject_unknown_hosts:
        client.set_missing_host_key_policy(ssh.AutoAddPolicy())

    #
    # Connection attempt loop
    #

    # Initialize loop variables
    connected = False
    password = get_password()
    tries = 0

    # Loop until successful connect (keep prompting for new password)
    while not connected:
        # Attempt connection
        try:
            tries += 1
            client.connect(
                hostname=host,
                port=int(port),
                username=user,
                password=password,
                key_filename=key_filenames(),
                timeout=env.timeout,
                allow_agent=not env.no_agent,
                look_for_keys=not env.no_keys
            )
            connected = True

            # set a keepalive if desired
            if env.keepalive:
                client.get_transport().set_keepalive(env.keepalive)

            return client
        # BadHostKeyException corresponds to key mismatch, i.e. what on the
        # command line results in the big banner error about man-in-the-middle
        # attacks.
        except ssh.BadHostKeyException, e:
            raise NetworkError("Host key for %s did not match pre-existing key! Server's key was changed recently, or possible man-in-the-middle attack." % env.host, e)
        # Prompt for new password to try on auth failure
        except (
            ssh.AuthenticationException,
            ssh.PasswordRequiredException,
            ssh.SSHException
        ), e:
            # For whatever reason, empty password + no ssh key or agent results
            # in an SSHException instead of an AuthenticationException. Since
            # it's difficult to do otherwise, we must assume empty password +
            # SSHException == auth exception. Conversely: if we get
            # SSHException and there *was* a password -- it is probably
            # something non auth related, and should be sent upwards.
            if e.__class__ is ssh.SSHException and password:
                raise NetworkError(str(e), e)

            # Otherwise, assume an auth exception, and prompt for new/better
            # password.

            # The 'ssh' library doesn't handle prompting for locked private
            # keys (i.e.  keys with a passphrase and not loaded into an agent)
            # so we have to detect this and tweak our prompt slightly.
            # (Otherwise, however, the logic flow is the same, because
            # ssh's connect() method overrides the password argument to be
            # either the login password OR the private key passphrase. Meh.)
            #
            # NOTE: This will come up if you normally use a
            # passphrase-protected private key with ssh-agent, and enter an
            # incorrect remote username, because ssh.connect:
            # * Tries the agent first, which will fail as you gave the wrong
            # username, so obviously any loaded keys aren't gonna work for a
            # nonexistent remote account;
            # * Then tries the on-disk key file, which is passphrased;
            # * Realizes there's no password to try unlocking that key with,
            # because you didn't enter a password, because you're using
            # ssh-agent;
            # * In this condition (trying a key file, password is None)
            # ssh raises PasswordRequiredException.
            text = None
            if e.__class__ is ssh.PasswordRequiredException:
                # NOTE: we can't easily say WHICH key's passphrase is needed,
                # because ssh doesn't provide us with that info, and
                # env.key_filename may be a list of keys, so we can't know
                # which one raised the exception. Best not to try.
                prompt = "[%s] Passphrase for private key"
                text = prompt % env.host_string
            password = prompt_for_password(text)
            # Update env.password, env.passwords if empty
            set_password(password)
        # Ctrl-D / Ctrl-C for exit
        except (EOFError, TypeError):
            # Print a newline (in case user was sitting at prompt)
            print('')
            sys.exit(0)
        # Handle DNS error / name lookup failure
        except socket.gaierror, e:
            raise NetworkError('Name lookup failed for %s' % host, e)
        # Handle timeouts and retries, including generic errors
        # NOTE: In 2.6, socket.error subclasses IOError
        except socket.error, e:
            not_timeout = type(e) is not socket.timeout
            giving_up = tries >= env.connection_attempts
            # Baseline error msg for when debug is off
            msg = "Timed out trying to connect to %s" % host
            # Expanded for debug on
            err = msg + " (attempt %s of %s)" % (tries, env.connection_attempts)
            if giving_up:
                err += ", giving up"
            err += ")"
            # Debuggin'
            if output.debug:
                print >>sys.stderr, err
            # Having said our piece, try again
            if not giving_up:
                # Sleep if it wasn't a timeout, so we still get timeout-like
                # behavior
                if not_timeout:
                    time.sleep(env.timeout)
                continue
            # Override eror msg if we were retrying other errors
            if not_timeout:
                msg = "Low level socket error connecting to host %s: %s" % (
                    host, e[1]
                )
            # Here, all attempts failed. Tweak error msg to show # tries.
            # TODO: find good humanization module, jeez
            s = "s" if env.connection_attempts > 1 else ""
            msg += " (tried %s time%s)" % (env.connection_attempts, s)
            raise NetworkError(msg, e)


def prompt_for_password(prompt=None, no_colon=False, stream=None):
    """
    Prompts for and returns a new password if required; otherwise, returns
    None.

    A trailing colon is appended unless ``no_colon`` is True.

    If the user supplies an empty password, the user will be re-prompted until
    they enter a non-empty password.

    ``prompt_for_password`` autogenerates the user prompt based on the current
    host being connected to. To override this, specify a string value for
    ``prompt``.

    ``stream`` is the stream the prompt will be printed to; if not given,
    defaults to ``sys.stderr``.
    """
    from fabric.state import env
    handle_prompt_abort("a connection or sudo password")
    stream = stream or sys.stderr
    # Construct prompt
    default = "[%s] Login password" % env.host_string
    password_prompt = prompt if (prompt is not None) else default
    if not no_colon:
        password_prompt += ": "
    # Get new password value
    new_password = getpass.getpass(password_prompt, stream)
    # Otherwise, loop until user gives us a non-empty password (to prevent
    # returning the empty string, and to avoid unnecessary network overhead.)
    while not new_password:
        print("Sorry, you can't enter an empty password. Please try again.")
        new_password = getpass.getpass(password_prompt, stream)
    return new_password


def needs_host(func):
    """
    Prompt user for value of ``env.host_string`` when ``env.host_string`` is
    empty.

    This decorator is basically a safety net for silly users who forgot to
    specify the host/host list in one way or another. It should be used to wrap
    operations which require a network connection.

    Due to how we execute commands per-host in ``main()``, it's not possible to
    specify multiple hosts at this point in time, so only a single host will be
    prompted for.

    Because this decorator sets ``env.host_string``, it will prompt once (and
    only once) per command. As ``main()`` clears ``env.host_string`` between
    commands, this decorator will also end up prompting the user once per
    command (in the case where multiple commands have no hosts set, of course.)
    """
    from fabric.state import env
    @wraps(func)
    def host_prompting_wrapper(*args, **kwargs):
        while not env.get('host_string', False):
            handle_prompt_abort("the target host connection string")
            host_string = raw_input("No hosts found. Please specify (single)"
                                    " host string for connection: ")
            env.update(to_dict(host_string))
        return func(*args, **kwargs)
    return host_prompting_wrapper


def disconnect_all():
    """
    Disconnect from all currently connected servers.

    Used at the end of ``fab``'s main loop, and also intended for use by
    library users.
    """
    from fabric.state import connections, output
    # Explicitly disconnect from all servers
    for key in connections.keys():
        if output.status:
            print "Disconnecting from %s..." % denormalize(key),
        connections[key].close()
        del connections[key]
        if output.status:
            print "done."
