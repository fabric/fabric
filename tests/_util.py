from itertools import chain, repeat
import os
import sys
import types
from functools import wraps, partial
from invoke.vendor.six import StringIO

from fabric import Connection
from fabric.main import program as fab_program
from fabric.transfer import Transfer
from mock import patch, Mock, PropertyMock, call, ANY
from spec import eq_, trap


# TODO: figure out a non shite way to share Invoke's more beefy copy of same.
@trap
def expect(invocation, out, program=None, test=None):
    if program is None:
        program = fab_program
    program.run("fab {0}".format(invocation), exit=False)
    (test or eq_)(sys.stdout.getvalue(), out)


class Command(object):
    """
    Data record specifying params of a command execution to mock/expect.

    :param str cmd:
        Command string to expect. If not given, no expectations about the
        command executed will be set up. Default: ``None``.

    :param str out: Data yielded as remote stdout. Default: ``""``.

    :param str err: Data yielded as remote stderr. Default: ``""``.

    :param int exit: Remote exit code. Default: ``0``.

    :param int waits:
        Number of calls to the channel's ``exit_status_ready`` that should
        return ``False`` before it then returns ``True``. Default: ``0``
        (``exit_status_ready`` will return ``True`` immediately).
    """
    def __init__(self, cmd=None, out="", err="", exit=0, waits=0):
        self.cmd = cmd
        self.out = out
        self.err = err
        self.exit = exit
        self.waits = waits


class Session(object):
    """
    A mock remote session of a single connection and 1 or more command execs.

    Allows quick configuration of expected remote state, and also helps
    generate the necessary test mocks used by `.mock_remote` itself. Only
    useful when handed into `.mock_remote`.

    The parameters ``cmd``, ``out``, ``err``, ``exit`` and ``waits`` are all
    shorthand for the same constructor arguments for a single anonymous
    `.Command`; see `.Command` for details.

    To give fully explicit `.Command` objects, use the ``commands`` parameter.

    :param str host:
        Which hostname to expect a connection to. If given, will cause a test
        failure if a connection is made to a different host instead. Default:
        ``None``.

    :param commands:
        Iterable of `.Command` objects, used when mocking nontrivial sessions
        involving >1 command execution per host. Default: ``None``.

        .. note::
            Giving ``cmd``, ``out`` etc alongside explicit ``commands`` is not
            allowed and will result in an error.
    """
    def __init__(
        self,
        host=None,
        commands=None,
        cmd=None,
        out=None,
        err=None,
        exit=None,
        waits=None
    ):
        # Sanity check
        params = (cmd or out or err or exit or waits)
        if commands and params:
            raise ValueError("You can't give both 'commands' and individual Command parameters!") # noqa
        # Fill in values
        self.host = host
        self.commands = commands
        if params:
            # Honestly dunno which is dumber, this or duplicating Command's
            # default kwarg values in this method's signature...sigh
            kwargs = {}
            if cmd is not None:
                kwargs['cmd'] = cmd
            if out is not None:
                kwargs['out'] = out
            if err is not None:
                kwargs['err'] = err
            if exit is not None:
                kwargs['exit'] = exit
            if waits is not None:
                kwargs['waits'] = waits
            self.commands = [Command(**kwargs)]
        if not self.commands:
            self.commands = [Command()]

    def generate_mocks(self):
        """
        Sets up a mock `.SSHClient` and one or more mock `Channel` objects.

        Specifically, the client will expect itself to be connected to
        ``self.host`` (if given), the channels will be associated with the
        client's `.Transport`, and the channels will expect/provide
        command-execution behavior as specified on the `.Command` objects
        supplied to this `.Session`.

        The client is then attached as ``self.client`` and the channels as
        ``self.channels`.

        :returns:
            ``None`` - this is mostly a "deferred setup" method and callers
            will just reference the above attributes (and call more methods) as
            needed.
        """
        client = Mock()
        transport = client.get_transport.return_value # another Mock

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
            channel = Mock()
            channel.recv_exit_status.return_value = command.exit

            # If requested, make exit_status_ready return False the first N
            # times it is called in the wait() loop.
            readies = chain(repeat(False, command.waits), repeat(True))
            channel.exit_status_ready.side_effect = readies

            # Real-feeling IO (not just returning whole strings)
            out_file = StringIO(command.out)
            err_file = StringIO(command.err)
            def fakeread(count, fileno=None):
                fd = {1: out_file, 2: err_file}[fileno]
                return fd.read(count)
            channel.recv.side_effect = partial(fakeread, fileno=1)
            channel.recv_stderr.side_effect = partial(fakeread, fileno=2)

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
        # TODO: give a shit about port too
        self.client.connect.assert_called_once_with(
            hostname=self.host or ANY,
            port=ANY
        )

        # And per-run() we expect a single session open, connect and
        # command_exec. Bundle them up so that by end of run we can ensure we
        # only got the calls expected.
        session_opens = []
        command_execs = []

        for channel, command in zip(self.channels, self.commands):
            # Expect an open_session for each command exec
            session_opens.append(call())
            # Expect that the channel gets an exec_command
            channel.exec_command.assert_called_with(command.cmd or ANY)

        # Test equality to actual call lists recorded
        eq_(transport.return_value.open_session.call_args_list, session_opens)


def mock_remote(*sessions):
    """
    Mock & expect one or more remote connections & command executions.

    With no parameterization (``@mock_remote``) or empty parameterization
    (``@mock_remote()``) a single default connection+execution is implied, i.e,
    equivalent to ``@mock_remote(Session())``.

    When parameterized, takes `.Session` objects (see warning below about
    ordering).

    .. warning::
        Due to ``SSHClient``'s API, we must expect connections in the order
        that they are made. If you run into failures caused by explicitly
        expecting hosts in this manner, **make sure** the order of sessions
        and commands you're giving ``@mock_remote`` matches the order in
        which the code under test is creating new ``SSHClient`` objects!

    The wrapped test function must accept a positional argument for each command
    in ``*sessions``, which are used to hand in the mock channel objects that
    are created (so that the test function may make asserts with them).

    .. note::
        The actual logic involved is a flattening of all commands across the
        sessions, to make accessing them within the tests fast and easy. E.g.
        in this test setup::

            @mock_remote(
                Session(Command('whoami'), Command('uname')),
                Session(host='foo', cmd='ls /'),
            )

        you would want to set up the test signature for 3 command channels::

            @mock_remote(...)
            def mytest(self, chan_whoami, chan_uname, chan_ls):
                pass

        Most of the time, however, there is a 1:1 map between session and
        command, making this straightforward.
    """
    # Was called as bare decorator, no args
    bare = (
        len(sessions) == 1
        and isinstance(sessions[0], types.FunctionType)
    )
    if bare:
        func = sessions[0]
        sessions = []
    # Either bare or called with empty parens
    if not sessions:
        sessions = [Session()]

    def decorator(f):
        @wraps(f)
        @patch('fabric.connection.SSHClient')
        @patch('fabric.runners.time')
        def wrapper(*args, **kwargs):
            args = list(args)
            SSHClient, time = args.pop(), args.pop()

            # Mock clients, to be inspected afterwards during sanity-checks
            clients = []
            # The channels of those clients, for handing into test function
            all_channels = []
            for session in sessions:
                session.generate_mocks()
                clients.append(session.client)
                all_channels.extend(session.channels)

            # Each time the mocked SSHClient class is instantiated, it will
            # yield one of our mocked clients (w/ mocked transport & channel)
            # generated above.
            SSHClient.side_effect = clients

            # Run test, passing in the channels involved for asserts/etc
            args.extend(chain.from_iterable(x.channels for x in sessions))
            f(*args, **kwargs)

            # Post-execution sanity checks
            for session in sessions:
                # Basic stuff about transport, channel etc
                session.sanity_check()
            # Internals call time.sleep() while waiting and we want to ensure
            # that this happened as many times as expected. Due to it being a
            # stdlib/global call, best we can do is make assertions about the
            # total number of calls - can't pin them down to individual
            # sessions/clients/channels.
            total_waits = sum(
                cmd.waits
                for cmd in session.commands
                for session in sessions
            )
            # TODO: be more explicit, make this "a bunch of call(1)'s"?
            eq_(time.sleep.call_count, total_waits)
        return wrapper
    # Bare decorator, no args
    if bare:
        return decorator(func)
    # Args were given
    else:
        return decorator


# TODO: dig harder into spec setup() treatment to figure out why it seems to be
# double-running setup() or having one mock created per nesting level...then we
# won't need this probably.
def mock_sftp(expose_os=False):
    """
    Mock SFTP things, including 'os' & handy ref to SFTPClient instance.

    By default, hands decorated tests a reference to the mocked SFTPClient
    instance and an instantiated Transfer instance, so their signature needs to
    be: ``def xxx(self, sftp, transfer):``.

    If ``expose_os=True``, the mocked ``os`` module is handed in, turning the
    signature to: ``def xxx(self, sftp, transfer, mock_os):``.
    """
    def decorator(f):
        @wraps(f)
        @patch('fabric.transfer.os')
        @patch('fabric.connection.SSHClient')
        def wrapper(*args, **kwargs):
            # Obtain the mocks given us by @patch (and 'self')
            self, Client, mock_os = args
            # SFTP client instance mock
            sftp = Client.return_value.open_sftp.return_value
            # All mock_sftp'd tests care about a Transfer instance
            transfer = Transfer(Connection('host'))
            # Handle common filepath massage actions; tests will assume these.
            def fake_abspath(path):
                return '/local/{0}'.format(path)
            mock_os.path.abspath.side_effect = fake_abspath
            sftp.getcwd.return_value = '/remote'
            # Not super clear to me why the 'wraps' functionality in mock isn't
            # working for this :(
            mock_os.path.basename.side_effect = os.path.basename
            # Pass in mocks as needed
            passed_args = [self, sftp, transfer]
            if expose_os:
                passed_args.append(mock_os)
            # TEST!
            return f(*passed_args)
        return wrapper
    return decorator
