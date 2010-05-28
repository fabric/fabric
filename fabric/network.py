"""
Classes and subroutines dealing with network connections and related topics.
"""

from functools import wraps
import getpass
import re
import threading
import socket
import sys

from fabric.utils import abort

try:
    import warnings
    warnings.simplefilter('ignore', DeprecationWarning)
    import paramiko as ssh
except ImportError:
    abort("paramiko is a required module. Please install it:\n\t$ sudo easy_install paramiko")



host_pattern = r'((?P<user>[^@]+)@)?(?P<host>[^:]+)(:(?P<port>\d+))?'
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
    def __getitem__(self, key):
        # Normalize given key (i.e. obtain username and port, if not given)
        user, host, port = normalize(key)
        # Recombine for use as a key.
        real_key = join_host_strings(user, host, port)
        # If not found, create new connection and store it
        if real_key not in self:
            self[real_key] = connect(user, host, port)
        # Return the value either way
        return dict.__getitem__(self, real_key)


def normalize(host_string, omit_port=False):
    """
    Normalizes a given host string, returning explicit host, user, port.

    If ``omit_port`` is given and is True, only the host and user are returned.
    """
    from fabric.state import env
    # Gracefully handle "empty" input by returning empty output
    if not host_string:
        return ('', '') if omit_port else ('', '', '')
    # Get user, host and port separately
    r = host_regex.match(host_string).groupdict()
    # Add any necessary defaults in
    user = r['user'] or env.get('user')
    host = r['host']
    port = r['port'] or '22'
    if omit_port:
        return user, host
    return user, host, port


def denormalize(host_string):
    """
    Strips out default values for the given host string.

    If the user part is the default user, it is removed; if the port is port 22,
    it also is removed.
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

    This function is not responsible for handling missing user/port strings; for
    that, see the ``normalize`` function.

    If ``port`` is omitted, the returned string will be of the form
    ``user@host``.
    """
    port_string = ''
    if port:
        port_string = ":%s" % port
    return "%s@%s%s" % (user, host, port_string)


def connect(user, host, port):
    """
    Create and return a new SSHClient instance connected to given host.
    """
    from state import env

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
    password = env.password

    # Loop until successful connect (keep prompting for new password)
    while not connected:
        # Attempt connection
        try:
            client.connect(
                hostname=host,
                port=int(port),
                username=user,
                password=password,
                key_filename=env.key_filename,
                timeout=10,
                allow_agent=not env.no_agent,
                look_for_keys=not env.no_keys
            )
            connected = True
            return client
        # BadHostKeyException corresponds to key mismatch, i.e. what on the
        # command line results in the big banner error about man-in-the-middle
        # attacks.
        except ssh.BadHostKeyException:
            abort("Host key for %s did not match pre-existing key! Server's key was changed recently, or possible man-in-the-middle attack." % env.host)
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
                abort(str(e))

            # Otherwise, assume an auth exception, and prompt for new/better
            # password.

            # Paramiko doesn't handle prompting for locked private keys (i.e.
            # keys with a passphrase and not loaded into an agent) so we have
            # to detect this and tweak our prompt slightly.  (Otherwise,
            # however, the logic flow is the same, because Paramiko's connect()
            # method overrides the password argument to be either the login
            # password OR the private key passphrase. Meh.)
            #
            # NOTE: This will come up if you normally use a
            # passphrase-protected private key with ssh-agent, and enter an
            # incorrect remote username, because Paramiko:
            # * Tries the agent first, which will fail as you gave the wrong
            # username, so obviously any loaded keys aren't gonna work for a
            # nonexistent remote account;
            # * Then tries the on-disk key file, which is passphrased;
            # * Realizes there's no password to try unlocking that key with,
            # because you didn't enter a password, because you're using
            # ssh-agent;
            # * In this condition (trying a key file, password is None)
            # Paramiko raises PasswordRequiredException.
            text = None
            if e.__class__ is ssh.PasswordRequiredException:
                # NOTE: we can't easily say WHICH key's passphrase is needed,
                # because Paramiko doesn't provide us with that info, and
                # env.key_filename may be a list of keys, so we can't know
                # which one raised the exception. Best not to try.
                text = "Please enter passphrase for private key"
            password = prompt_for_password(password, text)
            # Update env.password if it was empty
            if not env.password:
                env.password = password
        # Ctrl-D / Ctrl-C for exit
        except (EOFError, TypeError):
            # Print a newline (in case user was sitting at prompt)
            print('')
            sys.exit(0)
        # Handle timeouts
        except socket.timeout:
            abort('Timed out trying to connect to %s' % host)
        # Handle DNS error / name lookup failure
        except socket.gaierror:
            abort('Name lookup failed for %s' % host)
        # Handle generic network-related errors
        # NOTE: In 2.6, socket.error subclasses IOError
        except socket.error, e:
            abort('Low level socket error connecting to host %s: %s' % (
                host, e[1])
            )


def prompt_for_password(previous=None, prompt=None):
    """
    Prompts for and returns a new password if required; otherwise, returns None.

    ``previous`` should be the last known password, and is typically "primed"
    with ``env.password``, though it may be empty or None if ``env.password``
    was not set and no password has previously been entered during this
    session.

    When non-empty, ``previous`` will be used as a default if the user hits
    Enter without entering a new password, and the displayed password prompt
    will reflect this.

    If the user supplies an empty password **and** ``previous`` is also empty,
    the user will be re-prompted until they enter a non-empty password.

    Finally, ``prompt_for_password`` autogenerates the user prompt based on the
    current host being connected to. To override this, specify a string value
    for ``prompt``.
    """
    from fabric.state import env
    # Construct the prompt we will display to the user (using host if available)
    if 'host' in env:
        host = join_host_strings(*normalize(env.host_string, omit_port=True))
        base_password_prompt = "Password for %s" % host
    else:
        base_password_prompt = "Password"
    password_prompt = base_password_prompt
    # Handle prompt text override
    if prompt is not None:
        password_prompt = prompt
    # If the caller knew of a previously given password, give the user the
    # option of trying that again.
    if previous:
        password_prompt += " [Enter for previous]"
    password_prompt += ": "
    # Get new password value
    new_password = getpass.getpass(password_prompt)
    # See if user wants us to use the previous password and return right away
    # if so.
    if (not new_password) and previous:
        return previous
    # Otherwise, loop until user gives us a non-empty password (to prevent
    # returning the empty string, and to avoid unnecessary network overhead.)
    while not new_password:
        print("Sorry, you can't enter an empty password. Please try again.")
        password_prompt = base_password_prompt + ": "
        new_password = getpass.getpass(password_prompt)
    return new_password


def output_thread(prefix, chan, stderr=False, capture=None):
    """
    Generates a thread/function capable of reading and optionally capturing
    input from the given channel object ``chan``. ``stderr`` determines whether
    the channel's stdout or stderr is the focus of this particular thread.
    """
    from state import env, output

    def outputter(prefix, chan, stderr, capture):
        # Read one "packet" at a time, which lets us get less-than-a-line
        # chunks of text, such as sudo prompts. However, we still print
        # them to the user one line at a time. (We also eat sudo prompts.)
        leftovers = ""
        password = env.password
        if stderr:
            recv = chan.recv_stderr
        else:
            recv = chan.recv
        out = recv(65535)
        while out != '':
            # Capture if necessary
            if capture is not None:
                capture += out
            # Detect password prompts
            initial = re.findall(r'^%s$' % env.sudo_prompt, out, re.I|re.M)
            try_again = re.findall(r'^Sorry, try again', out, re.I|re.M)
            # Deal with any such prompts
            if initial or try_again:
                # Prompt user if nothing to try, or if stored password failed
                if not password or try_again:
                    password = prompt_for_password(password)
                # Set environment password if that was previously empty.
                if not env.password:
                    env.password = password
                # Send current password down the pipe
                chan.sendall(password + '\n')
                out = ""
            # Deal with line breaks, printing all lines and storing the
            # leftovers, if any.
            if '\n' in out or '\r' in out:
                # Break into list of lines/parts
                parts = out.splitlines()
                # Deal with edge case of trailing newline (messes up leftovers
                # logic due to how splitlines() behaves)
                if out[-1] in ['\n', '\r']:
                    parts.append('')
                # Initialize loop with first line
                line = leftovers + parts.pop(0)
                # Take off the last part, since it may be a partial line
                if parts:
                    leftovers = parts.pop()
                while parts or line:
                    # Write stderr to our own stderr.
                    out_stream = stderr and sys.stderr or sys.stdout
                    # But only write at all if we're supposed to.
                    if ((not stderr and output.stdout)
                        or (stderr and output.stderr)):
                        out_stream.write("%s: %s\n" % (prefix, line)),
                        out_stream.flush()
                    if parts:
                        line = parts.pop(0)
                    else:
                        line = ""
            else: # add to leftovers buffer
                leftovers += out
            # Get next handful of bytes and continue the loop
            out = recv(65535)
    thread = threading.Thread(None, outputter, prefix,
        (prefix, chan, stderr, capture))
    thread.setDaemon(True)
    thread.start()
    return thread


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
            env.host_string = raw_input("No hosts found. Please specify (single) host string for connection: ")
        return func(*args, **kwargs)
    return host_prompting_wrapper
