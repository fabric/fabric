from itertools import chain, repeat
import os
import sys
import types
from functools import wraps, partial
from invoke.vendor.six import StringIO

from fabric import Connection
from fabric.main import program as fab_program
from fabric.transfer import Transfer
from mock import patch, Mock, PropertyMock
from spec import eq_, trap


# TODO: figure out a non shite way to share Invoke's more beefy copy of same.
@trap
def expect(invocation, out, program=None, test=None):
    if program is None:
        program = fab_program
    program.run("fab {0}".format(invocation), exit=False)
    (test or eq_)(sys.stdout.getvalue(), out)


# TODO: this needs to be more like real mocking where I can set up >1 per test
# with different expectations.
# TODO: it should default to what it is now, a single exec_command instance
# TODO: BUT it should error USEFULLY if something tries running >1 in a row.
# Right now we just run into (initially) exit_status_ready having a
# multiple-but-finite side_effect (due to how the 'wait' kwarg works) - which
# is not a useful error.
# TODO: so what should happen is transport.open_session needs to die usefully
# if it's called more times than expected, since it maps to calls to run().
# TODO: but that only gets us so far, we probably need more
# funcs-as-side_effects which know to barf if they're called w/ unexpected
# shit, that would allow us to say "ok I want to allow SSHClients to X and Y,
# and only one run() on each" or "one run() on X returning blah stdout, two
# runs on Y returning biz and baz stdouts".
# TODO: it'd be ideal for these to work as orthogonally-composing decorators,
# but may be easier as a single decorator with more flexible args somehow? e.g.
# a *args of dicts with out/err/exit/wait keys, or a **kwargs of hostname keys
# mapping to array of those? @mock_remote(host1={'out': 'lol butts'}) for
# example.
# TODO: tho still gotta figure out how to say "expect 'the default' (no
# out/err, exit 0, wait 0) for host 'foo'", maybe that's another use of *args?
def mock_remote(*executions, **hosts):
    """
    Mock & expect one or more remote connections & command executions.

    By default, with no parameterization, a single generic "connect and execute
    a command" session is implied, returning empty strings for stdout/stderr,
    exiting with exit code 0, and where ``exit_status_ready`` returns ``True``
    immediately.

    Positional arguments (if given) should be dicts, each mapping to a single
    connect-and-execute session, with the following possible keys & values:

    * ``out`` and/or ``err``: strings yielded as the respective remote stream,
      default: ``""``.
    * ``exit``: integer of remote exit code, default: ``0``.
    * ``wait``: how many calls to the channel's ``exit_status_ready`` should
      return ``False`` before they return ``True``. Default: ``0``
      (``exit_status_ready`` will return ``True`` the very first time).

    Keyword arguments (if given) should map expected hostnames to dicts of the
    format described just above. While the positional argument sessions don't
    place constraints on connection hostname, keyword-argument sessions will
    raise exceptions if hostnames don't match (i.e. ``@mock_remote(foo={...})``
    will fail a test if the code under test doesn't trigger a connection to
    host 'foo').

    The wrapped test function must accept positional and/or keyword arguments
    mirroring those given to ``mock_remote``, which will be used to transfer
    the mock channel objects that are created.
    """
    # Was called as bare decorator, no args
    bare = (
        len(executions) == 1
        and not hosts
        and isinstance(executions[0], types.FunctionType)
    )
    if bare:
        func = executions[0]
        executions = []
    def decorator(f):
        @wraps(f)
        @patch('fabric.connection.SSHClient')
        @patch('fabric.runners.time')
        def wrapper(*args, **kwargs):
            args = list(args)
            SSHClient, time = args.pop(), args.pop()

            # Mock out Paramiko bits we expect to be used for most run() calls
            def make_client(out, err, exit, wait):
                client = Mock()
                transport = client.get_transport.return_value # another Mock
                channel = Mock()

                # Connection.open() tests transport.active before calling
                # connect() So, needs to start out False, then be True
                # afterwards (at least in default "connection succeeded"
                # scenarios...)
                # NOTE: if transport.active is called more than expected (e.g.
                # for debugging purposes) that will goof this up :(
                actives = chain([False], repeat(True))
                # NOTE: setting PropertyMocks on a mock's type() is apparently
                # How It Must Be Done, otherwise it sets the real attr value.
                type(transport).active = PropertyMock(side_effect=actives)

                # Raise a useful exception if >1 session is called
                # per requested (in this decorator) client. Such implies that
                # more than one run() was executed per task.
                # TODO: be more flexible about expected connections vs run()
                # calls (which should be N-M, even though the
                # base case for testing is usually 1-1). Should be achievable
                # w/ kwargs (tho perhaps disallow use of both args and kwargs
                # since that starts to get messy - how do we know what to
                # return from SSHClient.side_effect in that case? with kwargs
                # it'd have to be using a real function mapping to hostnames,
                # so having anonymous arg-based connections is then ambiguous.
                transport.open_session.return_value = channel
                channel.recv_exit_status.return_value = exit

                # If requested, make exit_status_ready return False the first N
                # times it is called in the wait() loop.
                readies = chain(repeat(False, wait), repeat(True))
                channel.exit_status_ready.side_effect = readies

                # Real-feeling IO
                out_file = StringIO(out)
                err_file = StringIO(err)
                def fakeread(count, fileno=None):
                    fd = {1: out_file, 2: err_file}[fileno]
                    return fd.read(count)
                channel.recv.side_effect = partial(fakeread, fileno=1)
                channel.recv_stderr.side_effect = partial(fakeread, fileno=2)

                return client, channel

            my_executions = list(executions) if executions else [{}]

            clients = []
            channels = []
            waits = []
            for x in my_executions:
                wait = x.get('wait', 0)
                client, channel = make_client(
                    out=x.get('out', ""),
                    err=x.get('err', ""),
                    exit=x.get('exit', 0),
                    wait=wait,
                )
                clients.append(client)
                channels.append(channel)
                waits.append(wait)

            # Each time the mocked SSHClient class is instantiated, it will
            # yield one of our mocked clients (w/ mocked transport & channel)
            # generated above.
            SSHClient.side_effect = clients

            # Run test, passing in channel obj (as it's the most useful mock)
            # as last arg
            args.extend(channels)
            f(*args, **kwargs)

            # Sanity checks
            for client in clients:
                t = client.get_transport
                t.assert_called_with()
                t.return_value.open_session.assert_called_once_with()
            eq_(time.sleep.call_count, sum(waits))
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
