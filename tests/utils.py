from __future__ import with_statement

from StringIO import StringIO # No need for cStringIO at this time
from contextlib import contextmanager
from functools import wraps
import copy
import sys

from fabric.context_managers import settings
from fabric.network import interpret_host_string
from fabric.state import env

from server import PORT, mapping, users


class FabricTest(object):
    """
    Nose-oriented test runner class that wipes env after every test.
    """
    def setup(self):
        self.previous_env = copy.deepcopy(env)
        # Network stuff
        env.disable_known_hosts = True
        interpret_host_string('%s@localhost:%s' % (env.local_user, PORT))
        env.password = users[env.local_user]

    def teardown(self):
        env = copy.deepcopy(self.previous_env)


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
