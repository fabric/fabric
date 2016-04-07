"""
Context managers for use with the ``with`` statement.

.. note:: When using Python 2.5, you will need to start your fabfile
    with ``from __future__ import with_statement`` in order to make use of
    the ``with`` statement (which is a regular, non ``__future__`` feature of
    Python 2.6+.)

.. note:: If you are using multiple directly nested ``with`` statements, it can
    be convenient to use multiple context expressions in one single with
    statement. Instead of writing::

        with cd('/path/to/app'):
            with prefix('workon myvenv'):
                run('./manage.py syncdb')
                run('./manage.py loaddata myfixture')

    you can write::

        with cd('/path/to/app'), prefix('workon myvenv'):
            run('./manage.py syncdb')
            run('./manage.py loaddata myfixture')

    Note that you need Python 2.7+ for this to work. On Python 2.5 or 2.6, you
    can do the following::

        from contextlib import nested

        with nested(cd('/path/to/app'), prefix('workon myvenv')):
            ...

    Finally, note that `~fabric.context_managers.settings` implements
    ``nested`` itself -- see its API doc for details.
"""

from contextlib import contextmanager, nested
import socket
import select

from fabric.thread_handling import ThreadHandler
from fabric.state import output, win32, connections, env
from fabric import state
from fabric.utils import isatty

if not win32:
    import termios
    import tty


def _set_output(groups, which):
    """
    Refactored subroutine used by ``hide`` and ``show``.
    """
    previous = {}
    try:
        # Preserve original values, pull in new given value to use
        for group in output.expand_aliases(groups):
            previous[group] = output[group]
            output[group] = which
        # Yield control
        yield
    finally:
        # Restore original values
        output.update(previous)


def documented_contextmanager(func):
    wrapper = contextmanager(func)
    wrapper.undecorated = func
    return wrapper


@documented_contextmanager
def show(*groups):
    """
    Context manager for setting the given output ``groups`` to True.

    ``groups`` must be one or more strings naming the output groups defined in
    `~fabric.state.output`. The given groups will be set to True for the
    duration of the enclosed block, and restored to their previous value
    afterwards.

    For example, to turn on debug output (which is typically off by default)::

        def my_task():
            with show('debug'):
                run('ls /var/www')

    As almost all output groups are displayed by default, `show` is most useful
    for turning on the normally-hidden ``debug`` group, or when you know or
    suspect that code calling your own code is trying to hide output with
    `hide`.
    """
    return _set_output(groups, True)


@documented_contextmanager
def hide(*groups):
    """
    Context manager for setting the given output ``groups`` to False.

    ``groups`` must be one or more strings naming the output groups defined in
    `~fabric.state.output`. The given groups will be set to False for the
    duration of the enclosed block, and restored to their previous value
    afterwards.

    For example, to hide the "[hostname] run:" status lines, as well as
    preventing printout of stdout and stderr, one might use `hide` as follows::

        def my_task():
            with hide('running', 'stdout', 'stderr'):
                run('ls /var/www')
    """
    return _set_output(groups, False)


@documented_contextmanager
def _setenv(variables):
    """
    Context manager temporarily overriding ``env`` with given key/value pairs.

    A callable that returns a dict can also be passed. This is necessary when
    new values are being calculated from current values, in order to ensure that
    the "current" value is current at the time that the context is entered, not
    when the context manager is initialized. (See Issue #736.)

    This context manager is used internally by `settings` and is not intended
    to be used directly.
    """
    if callable(variables):
        variables = variables()
    clean_revert = variables.pop('clean_revert', False)
    previous = {}
    new = []
    for key, value in variables.iteritems():
        if key in state.env:
            previous[key] = state.env[key]
        else:
            new.append(key)
        state.env[key] = value
    try:
        yield
    finally:
        if clean_revert:
            for key, value in variables.iteritems():
                # If the current env value for this key still matches the
                # value we set it to beforehand, we are OK to revert it to the
                # pre-block value.
                if key in state.env and value == state.env[key]:
                    if key in previous:
                        state.env[key] = previous[key]
                    else:
                        del state.env[key]
        else:
            state.env.update(previous)
            for key in new:
                del state.env[key]


def settings(*args, **kwargs):
    """
    Nest context managers and/or override ``env`` variables.

    `settings` serves two purposes:

    * Most usefully, it allows temporary overriding/updating of ``env`` with
      any provided keyword arguments, e.g. ``with settings(user='foo'):``.
      Original values, if any, will be restored once the ``with`` block closes.

        * The keyword argument ``clean_revert`` has special meaning for
          ``settings`` itself (see below) and will be stripped out before
          execution.

    * In addition, it will use `contextlib.nested`_ to nest any given
      non-keyword arguments, which should be other context managers, e.g.
      ``with settings(hide('stderr'), show('stdout')):``.

    .. _contextlib.nested: http://docs.python.org/library/contextlib.html#contextlib.nested

    These behaviors may be specified at the same time if desired. An example
    will hopefully illustrate why this is considered useful::

        def my_task():
            with settings(
                hide('warnings', 'running', 'stdout', 'stderr'),
                warn_only=True
            ):
                if run('ls /etc/lsb-release'):
                    return 'Ubuntu'
                elif run('ls /etc/redhat-release'):
                    return 'RedHat'

    The above task executes a `run` statement, but will warn instead of
    aborting if the ``ls`` fails, and all output -- including the warning
    itself -- is prevented from printing to the user. The end result, in this
    scenario, is a completely silent task that allows the caller to figure out
    what type of system the remote host is, without incurring the handful of
    output that would normally occur.

    Thus, `settings` may be used to set any combination of environment
    variables in tandem with hiding (or showing) specific levels of output, or
    in tandem with any other piece of Fabric functionality implemented as a
    context manager.

    If ``clean_revert`` is set to ``True``, ``settings`` will **not** revert
    keys which are altered within the nested block, instead only reverting keys
    whose values remain the same as those given. More examples will make this
    clear; below is how ``settings`` operates normally::

        # Before the block, env.parallel defaults to False, host_string to None
        with settings(parallel=True, host_string='myhost'):
            # env.parallel is True
            # env.host_string is 'myhost'
            env.host_string = 'otherhost'
            # env.host_string is now 'otherhost'
        # Outside the block:
        # * env.parallel is False again
        # * env.host_string is None again

    The internal modification of ``env.host_string`` is nullified -- not always
    desirable. That's where ``clean_revert`` comes in::

        # Before the block, env.parallel defaults to False, host_string to None
        with settings(parallel=True, host_string='myhost', clean_revert=True):
            # env.parallel is True
            # env.host_string is 'myhost'
            env.host_string = 'otherhost'
            # env.host_string is now 'otherhost'
        # Outside the block:
        # * env.parallel is False again
        # * env.host_string remains 'otherhost'

    Brand new keys which did not exist in ``env`` prior to using ``settings``
    are also preserved if ``clean_revert`` is active. When ``False``, such keys
    are removed when the block exits.

    .. versionadded:: 1.4.1
        The ``clean_revert`` kwarg.
    """
    managers = list(args)
    if kwargs:
        managers.append(_setenv(kwargs))
    return nested(*managers)


def cd(path):
    """
    Context manager that keeps directory state when calling remote operations.

    Any calls to `run`, `sudo`, `get`, or `put` within the wrapped block will
    implicitly have a string similar to ``"cd <path> && "`` prefixed in order
    to give the sense that there is actually statefulness involved.

    .. note::
        `cd` only affects *remote* paths -- to modify *local* paths, use
        `~fabric.context_managers.lcd`.

    Because use of `cd` affects all such invocations, any code making use of
    those operations, such as much of the ``contrib`` section, will also be
    affected by use of `cd`.

    Like the actual 'cd' shell builtin, `cd` may be called with relative paths
    (keep in mind that your default starting directory is your remote user's
    ``$HOME``) and may be nested as well.

    Below is a "normal" attempt at using the shell 'cd', which doesn't work due
    to how shell-less SSH connections are implemented -- state is **not** kept
    between invocations of `run` or `sudo`::

        run('cd /var/www')
        run('ls')

    The above snippet will list the contents of the remote user's ``$HOME``
    instead of ``/var/www``. With `cd`, however, it will work as expected::

        with cd('/var/www'):
            run('ls') # Turns into "cd /var/www && ls"

    Finally, a demonstration (see inline comments) of nesting::

        with cd('/var/www'):
            run('ls') # cd /var/www && ls
            with cd('website1'):
                run('ls') # cd /var/www/website1 && ls

    .. note::

        This context manager is currently implemented by appending to (and, as
        always, restoring afterwards) the current value of an environment
        variable, ``env.cwd``. However, this implementation may change in the
        future, so we do not recommend manually altering ``env.cwd`` -- only
        the *behavior* of `cd` will have any guarantee of backwards
        compatibility.

    .. note::

        Space characters will be escaped automatically to make dealing with
        such directory names easier.

    .. versionchanged:: 1.0
        Applies to `get` and `put` in addition to the command-running
        operations.

    .. seealso:: `~fabric.context_managers.lcd`
    """
    return _change_cwd('cwd', path)


def lcd(path):
    """
    Context manager for updating local current working directory.

    This context manager is identical to `~fabric.context_managers.cd`, except
    that it changes a different env var (`lcwd`, instead of `cwd`) and thus
    only affects the invocation of `~fabric.operations.local` and the local
    arguments to `~fabric.operations.get`/`~fabric.operations.put`.

    Relative path arguments are relative to the local user's current working
    directory, which will vary depending on where Fabric (or Fabric-using code)
    was invoked. You can check what this is with `os.getcwd
    <http://docs.python.org/release/2.6/library/os.html#os.getcwd>`_. It may be
    useful to pin things relative to the location of the fabfile in use, which
    may be found in :ref:`env.real_fabfile <real-fabfile>`

    .. versionadded:: 1.0
    """
    return _change_cwd('lcwd', path)


def _change_cwd(which, path):
    path = path.replace(' ', '\ ')
    if state.env.get(which) and not path.startswith('/') and not path.startswith('~'):
        new_cwd = state.env.get(which) + '/' + path
    else:
        new_cwd = path
    return _setenv({which: new_cwd})


def path(path, behavior='append'):
    """
    Append the given ``path`` to the PATH used to execute any wrapped commands.

    Any calls to `run` or `sudo` within the wrapped block will implicitly have
    a string similar to ``"PATH=$PATH:<path> "`` prepended before the given
    command.

    You may customize the behavior of `path` by specifying the optional
    ``behavior`` keyword argument, as follows:

    * ``'append'``: append given path to the current ``$PATH``, e.g.
      ``PATH=$PATH:<path>``. This is the default behavior.
    * ``'prepend'``: prepend given path to the current ``$PATH``, e.g.
      ``PATH=<path>:$PATH``.
    * ``'replace'``: ignore previous value of ``$PATH`` altogether, e.g.
      ``PATH=<path>``.

    .. note::

        This context manager is currently implemented by modifying (and, as
        always, restoring afterwards) the current value of environment
        variables, ``env.path`` and ``env.path_behavior``. However, this
        implementation may change in the future, so we do not recommend
        manually altering them directly.

    .. versionadded:: 1.0
    """
    return _setenv({'path': path, 'path_behavior': behavior})


def prefix(command):
    """
    Prefix all wrapped `run`/`sudo` commands with given command plus ``&&``.

    This is nearly identical to `~fabric.operations.cd`, except that nested
    invocations append to a list of command strings instead of modifying a
    single string.

    Most of the time, you'll want to be using this alongside a shell script
    which alters shell state, such as ones which export or alter shell
    environment variables.

    For example, one of the most common uses of this tool is with the
    ``workon`` command from `virtualenvwrapper
    <http://www.doughellmann.com/projects/virtualenvwrapper/>`_::

        with prefix('workon myvenv'):
            run('./manage.py syncdb')

    In the above snippet, the actual shell command run would be this::

        $ workon myvenv && ./manage.py syncdb

    This context manager is compatible with `~fabric.context_managers.cd`, so
    if your virtualenv doesn't ``cd`` in its ``postactivate`` script, you could
    do the following::

        with cd('/path/to/app'):
            with prefix('workon myvenv'):
                run('./manage.py syncdb')
                run('./manage.py loaddata myfixture')

    Which would result in executions like so::

        $ cd /path/to/app && workon myvenv && ./manage.py syncdb
        $ cd /path/to/app && workon myvenv && ./manage.py loaddata myfixture

    Finally, as alluded to near the beginning,
    `~fabric.context_managers.prefix` may be nested if desired, e.g.::

        with prefix('workon myenv'):
            run('ls')
            with prefix('source /some/script'):
                run('touch a_file')

    The result::

        $ workon myenv && ls
        $ workon myenv && source /some/script && touch a_file

    Contrived, but hopefully illustrative.
    """
    return _setenv(lambda: {'command_prefixes': state.env.command_prefixes + [command]})


@documented_contextmanager
def char_buffered(pipe):
    """
    Force local terminal ``pipe`` be character, not line, buffered.

    Only applies on Unix-based systems; on Windows this is a no-op.
    """
    if win32 or not isatty(pipe):
        yield
    else:
        old_settings = termios.tcgetattr(pipe)
        tty.setcbreak(pipe)
        try:
            yield
        finally:
            termios.tcsetattr(pipe, termios.TCSADRAIN, old_settings)


def shell_env(**kw):
    """
    Set shell environment variables for wrapped commands.

    For example, the below shows how you might set a ZeroMQ related environment
    variable when installing a Python ZMQ library::

        with shell_env(ZMQ_DIR='/home/user/local'):
            run('pip install pyzmq')

    As with `~fabric.context_managers.prefix`, this effectively turns the
    ``run`` command into::

        $ export ZMQ_DIR='/home/user/local' && pip install pyzmq

    Multiple key-value pairs may be given simultaneously.

    .. note::
        If used to affect the behavior of `~fabric.operations.local` when
        running from a Windows localhost, ``SET`` commands will be used to
        implement this feature.
    """
    return _setenv({'shell_env': kw})


def _forwarder(chan, sock):
    # Bidirectionally forward data between a socket and a Paramiko channel.
    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()


@documented_contextmanager
def remote_tunnel(remote_port, local_port=None, local_host="localhost",
    remote_bind_address="127.0.0.1"):
    """
    Create a tunnel forwarding a locally-visible port to the remote target.

    For example, you can let the remote host access a database that is
    installed on the client host::

        # Map localhost:6379 on the server to localhost:6379 on the client,
        # so that the remote 'redis-cli' program ends up speaking to the local
        # redis-server.
        with remote_tunnel(6379):
            run("redis-cli -i")

    The database might be installed on a client only reachable from the client
    host (as opposed to *on* the client itself)::

        # Map localhost:6379 on the server to redis.internal:6379 on the client
        with remote_tunnel(6379, local_host="redis.internal")
            run("redis-cli -i")

    ``remote_tunnel`` accepts up to four arguments:

    * ``remote_port`` (mandatory) is the remote port to listen to.
    * ``local_port`` (optional) is the local port to connect to; the default is
      the same port as the remote one.
    * ``local_host`` (optional) is the locally-reachable computer (DNS name or
      IP address) to connect to; the default is ``localhost`` (that is, the
      same computer Fabric is running on).
    * ``remote_bind_address`` (optional) is the remote IP address to bind to
      for listening, on the current target. It should be an IP address assigned
      to an interface on the target (or a DNS name that resolves to such IP).
      You can use "0.0.0.0" to bind to all interfaces.

    .. note::
        By default, most SSH servers only allow remote tunnels to listen to the
        localhost interface (127.0.0.1). In these cases, `remote_bind_address`
        is ignored by the server, and the tunnel will listen only to 127.0.0.1.

    .. versionadded: 1.6
    """
    if local_port is None:
        local_port = remote_port

    sockets = []
    channels = []
    threads = []

    def accept(channel, (src_addr, src_port), (dest_addr, dest_port)):
        channels.append(channel)
        sock = socket.socket()
        sockets.append(sock)

        try:
            sock.connect((local_host, local_port))
        except Exception, e:
            print "[%s] rtunnel: cannot connect to %s:%d (from local)" % (env.host_string, local_host, local_port)
            channel.close()
            return

        print "[%s] rtunnel: opened reverse tunnel: %r -> %r -> %r"\
              % (env.host_string, channel.origin_addr,
                 channel.getpeername(), (local_host, local_port))

        th = ThreadHandler('fwd', _forwarder, channel, sock)
        threads.append(th)

    transport = connections[env.host_string].get_transport()
    transport.request_port_forward(remote_bind_address, remote_port, handler=accept)

    try:
        yield
    finally:
        for sock, chan, th in zip(sockets, channels, threads):
            sock.close()
            chan.close()
            th.thread.join()
            th.raise_if_needed()
        transport.cancel_port_forward(remote_bind_address, remote_port)


quiet = lambda: settings(hide('everything'), warn_only=True)
quiet.__doc__ = """
    Alias to ``settings(hide('everything'), warn_only=True)``.

    Useful for wrapping remote interrogative commands which you expect to fail
    occasionally, and/or which you want to silence.

    Example::

        with quiet():
            have_build_dir = run("test -e /tmp/build").succeeded

    When used in a task, the above snippet will not produce any ``run: test -e
    /tmp/build`` line, nor will any stdout/stderr display, and command failure
    is ignored.

    .. seealso::
        :ref:`env.warn_only <warn_only>`,
        `~fabric.context_managers.settings`,
        `~fabric.context_managers.hide`

    .. versionadded:: 1.5
"""


warn_only = lambda: settings(warn_only=True)
warn_only.__doc__ = """
    Alias to ``settings(warn_only=True)``.

    .. seealso::
        :ref:`env.warn_only <warn_only>`,
        `~fabric.context_managers.settings`,
        `~fabric.context_managers.quiet`
"""
