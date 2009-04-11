"""
Classes and subroutines dealing with network connections and related topics.
"""

import getpass
import re
import threading

import paramiko as ssh


host_pattern = r'((?P<username>\w+)@)?(?P<hostname>[\w.]+)(:(?P<port>\d+))?'
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

    When the username is not given, ``env.username`` is used; if
    ``env.username`` is not defined, the local system username is assumed.

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
        username, hostname, port = normalize(key)
        # Recombine for use as a key.
        real_key = join_host_strings(username, hostname, port)
        # If not found, create new connection and store it
        if real_key not in self:
            self[real_key] = connect(username, hostname, port)
        # Return the value either way
        return dict.__getitem__(self, real_key)


def normalize(host_string):
    """
    Normalizes a given host string, returning explicit host, user, port.
    """
    from fabric.state import env
    # Get user, hostname and port separately
    r = host_regex.match(host_string).groupdict()
    # Add any necessary defaults in
    username = r['username'] or env.get('username') or env.system_username
    hostname = r['hostname']
    port = r['port'] or '22'
    return username, hostname, port


def join_host_strings(username, hostname, port):
    """
    Turns user/host/port strings into ``user@host:port`` combined string.

    This function is not responsible for handling missing user/port strings; for
    that, see the ``normalize`` function.
    """
    return "%s@%s:%s" % (username, hostname, port)


def connect(username, hostname, port):
    """
    Create and return a new SSHClient instance connected to given hostname.
    """
    from fabric.state import env

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
                # Imply we'll reuse last one entered, in prompt suffix
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
            # Print a newline (in case user was sitting at prompt)
            print('')
            sys.exit(0)
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


def output_thread(prefix, chan, stderr=False, capture=None):
    """
    Generates a thread/function capable of reading and optionally capturing
    input from the given channel object ``chan``. ``stderr`` determines whether
    the channel's stdout or stderr is the focus of this particular thread.
    """
    from fabric.state import env

    def outputter(prefix, chan, stderr, capture):
        # Read one "packet" at a time, which lets us get less-than-a-line
        # chunks of text, such as sudo prompts. However, we still print
        # them to the user one line at a time. (We also eat sudo prompts.)
        leftovers = ""
        suffix = ""
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
            # Handle any password prompts
            # TODO: tie this into global/centralized prompt detection
            initial_prompt = re.findall(r'^%s$' % env.sudo_prompt, out,
                re.I|re.M)
            again_prompt = re.findall(r'^Sorry, try again', out, re.I|re.M)
            if initial_prompt or again_prompt:
                # First, get or prompt for password
                password_prompt = ("Password for %s%s" % (env.host, suffix))
                if password:
                    # Just set up prompt in case we're at an again prompt
                    suffix = " [Enter for previous]: "
                else:
                    # Set prompt, then ask for a password
                    suffix = ": "
                    # Get pass, and make sure we communicate it back to the
                    # global environment since that was obviously empty.
                    env.password = password = getpass.getpass(password_prompt)
                # Re-prompt -- whatever we supplied last time (the
                # current value of env.password) was incorrect.
                # Don't overwrite env.password, though -- it may still be
                # correct for *other* hosts in a multi-host operation.
                if again_prompt:
                    password = getpass.getpass(password_prompt)
                # Either way, we have a password now, so send it.
                chan.sendall(password + '\n')
                out = ""
            # Deal with line breaks, printing all lines and storing the
            # leftovers, if any.
            if '\n' in out:
                parts = out.split('\n')
                line = leftovers + parts.pop(0)
                leftovers = parts.pop()
                while parts or line:
                    # TODO: tie in with global output controls
                    if not env.quiet:
                        sys.stdout.write("%s: %s\n" % (prefix, line)),
                        sys.stdout.flush()
                    if parts:
                        line = parts.pop(0)
                    else:
                        line = ""
            else: # add to leftovers buffer
                leftovers += out
            out = recv(65535)
    thread = threading.Thread(None, outputter, prefix,
        (prefix, chan, stderr, capture))
    thread.setDaemon(True)
    thread.start()
    return thread
