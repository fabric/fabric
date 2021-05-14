"""
This module contains helpers/fixtures to assist in testing Fabric-driven code.

It is not intended for production use, and pulls in some test-oriented
dependencies such as `mock <https://pypi.org/project/mock/>`_. You can install
an 'extra' variant of Fabric to get these dependencies if you aren't already
using them for your own testing purposes: ``pip install fabric[testing]``.

.. note::
    If you're using pytest for your test suite, you may be interested in
    grabbing ``fabric[pytest]`` instead, which encompasses the dependencies of
    both this module and the `fabric.testing.fixtures` module, which contains
    pytest fixtures.

.. versionadded:: 2.1
"""

from itertools import chain, repeat
from io import BytesIO
import os

try:
    from mock import Mock, PropertyMock, call, patch, ANY
except ImportError:
    import warnings

    warning = (
        "You appear to be missing some optional test-related dependencies;"
        "please 'pip install fabric[testing]'."
    )
    warnings.warn(warning, ImportWarning)
    raise


class Command(object):
    """
    Data record specifying params of a command execution to mock/expect.

    :param str cmd:
        Command string to expect. If not given, no expectations about the
        command executed will be set up. Default: ``None``.

    :param bytes out: Data yielded as remote stdout. Default: ``b""``.

    :param bytes err: Data yielded as remote stderr. Default: ``b""``.

    :param int exit: Remote exit code. Default: ``0``.

    :param int waits:
        Number of calls to the channel's ``exit_status_ready`` that should
        return ``False`` before it then returns ``True``. Default: ``0``
        (``exit_status_ready`` will return ``True`` immediately).

    .. versionadded:: 2.1
    """

    def __init__(self, cmd=None, out=b"", err=b"", in_=None, exit=0, waits=0):
        self.cmd = cmd
        self.out = out
        self.err = err
        self.in_ = in_
        self.exit = exit
        self.waits = waits

    def __repr__(self):
        # TODO: just leverage attrs, maybe vendored into Invoke so we don't
        # grow more dependencies? Ehhh
        return "<{} cmd={!r}>".format(self.__class__.__name__, self.cmd)

    def expect_execution(self, channel):
        """
        Assert that the ``channel`` was used to run this command.

        .. versionadded:: 2.7
        """
        channel.exec_command.assert_called_with(self.cmd or ANY)


class ShellCommand(Command):
    """
    A pseudo-command that expects an interactive shell to be executed.

    .. versionadded:: 2.7
    """

    def expect_execution(self, channel):
        channel.invoke_shell.assert_called_once_with()


class MockChannel(Mock):
    """
    Mock subclass that tracks state for its ``recv(_stderr)?`` methods.

    Turns out abusing function closures inside MockRemote to track this state
    only worked for 1 command per session!

    .. versionadded:: 2.1
    """

    def __init__(self, *args, **kwargs):
        # TODO: worth accepting strings and doing the BytesIO setup ourselves?
        # Stored privately to avoid any possible collisions ever. shrug.
        object.__setattr__(self, "__stdout", kwargs.pop("stdout"))
        object.__setattr__(self, "__stderr", kwargs.pop("stderr"))
        # Stdin less private so it can be asserted about
        object.__setattr__(self, "_stdin", BytesIO())
        super(MockChannel, self).__init__(*args, **kwargs)

    def _get_child_mock(self, **kwargs):
        # Don't return our own class on sub-mocks.
        return Mock(**kwargs)

    def recv(self, count):
        return object.__getattribute__(self, "__stdout").read(count)

    def recv_stderr(self, count):
        return object.__getattribute__(self, "__stderr").read(count)

    def sendall(self, data):
        return object.__getattribute__(self, "_stdin").write(data)


class Session(object):
    """
    A mock remote session of a single connection and 1 or more command execs.

    Allows quick configuration of expected remote state, and also helps
    generate the necessary test mocks used by `MockRemote` itself. Only useful
    when handed into `MockRemote`.

    The parameters ``cmd``, ``out``, ``err``, ``exit`` and ``waits`` are all
    shorthand for the same constructor arguments for a single anonymous
    `.Command`; see `.Command` for details.

    To give fully explicit `.Command` objects, use the ``commands`` parameter.

    :param str user:
    :param str host:
    :param int port:
        Sets up expectations that a connection will be generated to the given
        user, host and/or port. If ``None`` (default), no expectations are
        generated / any value is accepted.

    :param commands:
        Iterable of `.Command` objects, used when mocking nontrivial sessions
        involving >1 command execution per host. Default: ``None``.

        .. note::
            Giving ``cmd``, ``out`` etc alongside explicit ``commands`` is not
            allowed and will result in an error.

    .. versionadded:: 2.1
    """

    def __init__(
        self,
        host=None,
        user=None,
        port=None,
        commands=None,
        cmd=None,
        out=None,
        in_=None,
        err=None,
        exit=None,
        waits=None,
    ):
        # Sanity check
        params = cmd or out or err or exit or waits
        if commands and params:
            raise ValueError(
                "You can't give both 'commands' and individual "
                "Command parameters!"
            )  # noqa
        # Fill in values
        self.host = host
        self.user = user
        self.port = port
        self.commands = commands
        if params:
            # Honestly dunno which is dumber, this or duplicating Command's
            # default kwarg values in this method's signature...sigh
            kwargs = {}
            if cmd is not None:
                kwargs["cmd"] = cmd
            if out is not None:
                kwargs["out"] = out
            if err is not None:
                kwargs["err"] = err
            if in_ is not None:
                kwargs["in_"] = in_
            if exit is not None:
                kwargs["exit"] = exit
            if waits is not None:
                kwargs["waits"] = waits
            self.commands = [Command(**kwargs)]
        if not self.commands:
            self.commands = [Command()]

    def generate_mocks(self):
        """
        Mocks `~paramiko.client.SSHClient` and `~paramiko.channel.Channel`.

        Specifically, the client will expect itself to be connected to
        ``self.host`` (if given), the channels will be associated with the
        client's `~paramiko.transport.Transport`, and the channels will
        expect/provide command-execution behavior as specified on the
        `.Command` objects supplied to this `.Session`.

        The client is then attached as ``self.client`` and the channels as
        ``self.channels``.

        :returns:
            ``None`` - this is mostly a "deferred setup" method and callers
            will just reference the above attributes (and call more methods) as
            needed.

        .. versionadded:: 2.1
        """
        client = Mock()
        transport = client.get_transport.return_value  # another Mock

        # NOTE: this originally did chain([False], repeat(True)) so that
        # get_transport().active was False initially, then True. However,
        # because we also have to consider when get_transport() comes back None
        # (which it does initially), the case where we get back a non-None
        # transport _and_ it's not active yet, isn't useful to test, and
        # complicates text expectations. So we don't, for now.
        actives = repeat(True)
        # NOTE: setting PropertyMocks on a mock's type() is apparently
        # How It Must Be Done, otherwise it sets the real attr value.
        type(transport).active = PropertyMock(side_effect=actives)

        channels = []
        for command in self.commands:
            # Mock of a Channel instance, not e.g. Channel-the-class.
            # Specifically, one that can track individual state for recv*().
            channel = MockChannel(
                stdout=BytesIO(command.out), stderr=BytesIO(command.err)
            )
            channel.recv_exit_status.return_value = command.exit

            # If requested, make exit_status_ready return False the first N
            # times it is called in the wait() loop.
            readies = chain(repeat(False, command.waits), repeat(True))
            channel.exit_status_ready.side_effect = readies

            channels.append(channel)

        # Have our transport yield those channel mocks in order when
        # open_session() is called.
        transport.open_session.side_effect = channels

        self.client = client
        self.channels = channels

    def sanity_check(self):
        # Per-session we expect a single transport get
        transport = self.client.get_transport
        transport.assert_called_once_with()
        # And a single connect to our target host.
        self.client.connect.assert_called_once_with(
            username=self.user or ANY,
            hostname=self.host or ANY,
            port=self.port or ANY,
        )

        # Calls to open_session will be 1-per-command but are on transport, not
        # channel, so we can only really inspect how many happened in
        # aggregate. Save a list for later comparison to call_args.
        session_opens = []

        for channel, command in zip(self.channels, self.commands):
            # Expect an open_session for each command exec
            session_opens.append(call())
            # Expect that the channel gets an exec_command or etc
            command.expect_execution(channel=channel)
            # Expect written stdin, if given
            if command.in_:
                assert channel._stdin.getvalue() == command.in_

        # Make sure open_session was called expected number of times.
        calls = transport.return_value.open_session.call_args_list
        assert calls == session_opens


class MockRemote(object):
    """
    Class representing mocked remote state.

    By default this class is set up for start/stop style patching as opposed to
    the more common context-manager or decorator approach; this is so it can be
    used in situations requiring setup/teardown semantics.

    Defaults to setting up a single anonymous `Session`, so it can be used as a
    "request & forget" pytest fixture. Users requiring detailed remote session
    expectations can call methods like `expect`, which wipe that anonymous
    Session & set up a new one instead.

    .. versionadded:: 2.1
    """

    def __init__(self):
        self.expect_sessions(Session())

    # TODO: make it easier to assume single session w/ >1 command?

    def expect(self, *args, **kwargs):
        """
        Convenience method for creating & 'expect'ing a single `Session`.

        Returns the single `MockChannel` yielded by that Session.

        .. versionadded:: 2.1
        """
        return self.expect_sessions(Session(*args, **kwargs))[0]

    def expect_sessions(self, *sessions):
        """
        Sets the mocked remote environment to expect the given ``sessions``.

        Returns a list of `MockChannel` objects, one per input `Session`.

        .. versionadded:: 2.1
        """
        # First, stop the default session to clean up its state, if it seems to
        # be running.
        self.stop()
        # Update sessions list with new session(s)
        self.sessions = sessions
        # And start patching again, returning mocked channels
        return self.start()

    def start(self):
        """
        Start patching SSHClient with the stored sessions, returning channels.

        .. versionadded:: 2.1
        """
        # Patch SSHClient so the sessions' generated mocks can be set as its
        # return values
        self.patcher = patcher = patch("fabric.connection.SSHClient")
        SSHClient = patcher.start()
        # Mock clients, to be inspected afterwards during sanity-checks
        clients = []
        for session in self.sessions:
            session.generate_mocks()
            clients.append(session.client)
        # Each time the mocked SSHClient class is instantiated, it will
        # yield one of our mocked clients (w/ mocked transport & channel)
        # generated above.
        SSHClient.side_effect = clients
        return list(chain.from_iterable(x.channels for x in self.sessions))

    def stop(self):
        """
        Stop patching SSHClient.

        .. versionadded:: 2.1
        """
        # Short circuit if we don't seem to have start()ed yet.
        if not hasattr(self, "patcher"):
            return
        # Stop patching SSHClient
        self.patcher.stop()

    def sanity(self):
        """
        Run post-execution sanity checks (usually 'was X called' tests.)

        .. versionadded:: 2.1
        """
        for session in self.sessions:
            # Basic sanity tests about transport, channel etc
            session.sanity_check()


# TODO: unify with the stuff in paramiko itself (now in its tests/conftest.py),
# they're quite distinct and really shouldn't be.
class MockSFTP(object):
    """
    Class managing mocked SFTP remote state.

    Used in start/stop fashion in eg doctests; wrapped in the SFTP fixtures in
    conftest.py for main use.

    .. versionadded:: 2.1
    """

    def __init__(self, autostart=True):
        if autostart:
            self.start()

    def start(self):
        # Set up mocks
        self.os_patcher = patch("fabric.transfer.os")
        self.client_patcher = patch("fabric.connection.SSHClient")
        self.path_patcher = patch("fabric.transfer.Path")
        mock_os = self.os_patcher.start()
        Client = self.client_patcher.start()
        self.path_patcher.start()
        sftp = Client.return_value.open_sftp.return_value

        # Handle common filepath massage actions; tests will assume these.
        def fake_abspath(path):
            # Run normpath to avoid tests not seeing abspath wrinkles (like
            # trailing slash chomping)
            return "/local/{}".format(os.path.normpath(path))

        mock_os.path.abspath.side_effect = fake_abspath
        sftp.getcwd.return_value = "/remote"
        # Ensure stat st_mode is a real number; Python 2 stat.S_IMODE doesn't
        # appear to care if it's handed a MagicMock, but Python 3's does (?!)
        fake_mode = 0o644  # arbitrary real-ish mode
        sftp.stat.return_value.st_mode = fake_mode
        mock_os.stat.return_value.st_mode = fake_mode
        # Not super clear to me why the 'wraps' functionality in mock isn't
        # working for this :( reinstate a bunch of os(.path) so it still works
        mock_os.sep = os.sep
        for name in ("basename", "split", "join", "normpath"):
            getattr(mock_os.path, name).side_effect = getattr(os.path, name)
        # Return the sftp and OS mocks for use by decorator use case.
        return sftp, mock_os

    def stop(self):
        self.os_patcher.stop()
        self.client_patcher.stop()
        self.path_patcher.stop()
