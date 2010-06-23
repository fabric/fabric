from __future__ import with_statement
from contextlib import contextmanager
from functools import wraps
from StringIO import StringIO # No need for cStringIO at this time
import sys

from fabric.context_managers import settings

from server import serve_response


def mock_streams(*which):
    """
    Replaces a stream with a ``StringIO`` during the test, then restores after.

    Must specify which stream (stdout, stderr, etc) via string args, e.g.::

        @mock_streams('stdout')
        def func():
            pass

        @mock_streams('stderr')
        def func():
            pass

        @mock_streams('stdout', 'stderr')
        def func()
            pass
    """
    def mocked_streams_decorator(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            if 'stdout' in which:
                my_stdout, sys.stdout = sys.stdout, StringIO()
            if 'stderr' in which:
                my_stderr, sys.stderr = sys.stderr, StringIO()
            result = func(*args, **kwargs)
            if 'stderr' in which:
                sys.stderr = my_stderr
            if 'stdout' in which:
                sys.stdout = my_stdout
            return result
        return inner_wrapper
    return mocked_streams_decorator


@contextmanager
def response(command, stdout, stderr="", status=0, port=2200):
    """
    Convenience callback to server.serve_response().

    In addition to calling serve_response(), also sets host string
    appropriately and disables known_hosts.
    """
    with settings(host_string='localhost:%s' % port, disable_known_hosts=True):
        thread = serve_response(command, stdout, stderr, status, port)
        yield
        thread.join()
