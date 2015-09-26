import os
import sys
from functools import wraps, partial
from invoke.vendor.six import StringIO

from fabric import Connection
from fabric.main import program as fab_program
from fabric.transfer import Transfer
from mock import patch, Mock
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
def mock_remote(*calls):
    """
    Mock one or more remote command executions.

    ``*calls`` may be an array of dicts whose keys are as follows:

    * ``out`` and/or ``err``: strings yielded as the respective remote stream,
      default: ``""``.
    * ``exit``: integer of remote exit code, default: ``0``.
    * ``wait``: how many calls to the channel's ``exit_status_ready`` should
      return ``False`` before they return ``True``. Default: ``0``
      (``exit_status_ready`` will return ``True`` the very first time).

    The wrapped test function must take one positional arg for each entry in
    ``calls``, as the mocked ``channel`` object for each will be passed in.

    If ``calls`` is empty, a single wholly-default call (i.e. empty out/err,
    exits 0, waits 0) is implied.
    """
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
                transport = client.get_transport.return_value
                channel = Mock()
                transport.open_session.return_value = channel
                channel.recv_exit_status.return_value = exit

                # If requested, make exit_status_ready return False the first N
                # times it is called in the wait() loop.
                channel.exit_status_ready.side_effect = (wait * [False]) + [True]

                # Real-feeling IO
                out_file = StringIO(out)
                err_file = StringIO(err)
                def fakeread(count, fileno=None):
                    fd = {1: out_file, 2: err_file}[fileno]
                    return fd.read(count)
                channel.recv.side_effect = partial(fakeread, fileno=1)
                channel.recv_stderr.side_effect = partial(fakeread, fileno=2)
                
                return client, channel

            my_calls = list(calls) if calls else [{}]

            clients = []
            channels = []
            waits = []
            for call in my_calls:
                wait = call.get('wait', 0)
                client, channel = make_client(
                    out=call.get('out', ""),
                    err=call.get('err', ""),
                    exit=call.get('exit', 0),
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
                client.get_transport.assert_called_with()
                client.get_transport.return_value.open_session.assert_called_with()
            eq_(time.sleep.call_count, sum(waits))
        return wrapper
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
