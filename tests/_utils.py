from functools import wraps, partial
from invoke.vendor.six import StringIO

from spec import eq_
from mock import patch, Mock


def mock_remote(out='', err='', exit=0, wait=0):
    def decorator(f):
        @wraps(f)
        @patch('fabric.connection.SSHClient')
        @patch('fabric.runners.time')
        def wrapper(*args, **kwargs):
            args = list(args)
            SSHClient, time = args.pop(), args.pop()

            # Mock out Paramiko bits we expect to be used for most run() calls
            client = SSHClient.return_value
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

            # Run test, passing in channel obj (as it's the most useful mock)
            # as last arg
            args.append(channel)
            f(*args, **kwargs)

            # Sanity checks
            client.get_transport.assert_called_with()
            client.get_transport.return_value.open_session.assert_called_with()
            eq_(time.sleep.call_count, wait)
        return wrapper
    return decorator
