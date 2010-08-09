from __future__ import with_statement

from StringIO import StringIO # No need for cStringIO at this time
from contextlib import contextmanager
from functools import wraps
import copy
import getpass
import re
import sys

from fudge import Fake, patched_context, clear_expectations

from fabric.context_managers import settings
from fabric.network import interpret_host_string
from fabric.state import env
import fabric.network

from server import PORT, PASSWORDS


class FabricTest(object):
    """
    Nose-oriented test runner class that wipes env after every test.
    """
    def setup(self):
        # Clear Fudge mock expectations
        clear_expectations()
        # Copy env for restoration in teardown
        self.previous_env = copy.deepcopy(env)
        # Set up default networking for test server
        env.disable_known_hosts = True
        interpret_host_string('%s@localhost:%s' % (env.local_user, PORT))
        env.password = PASSWORDS[env.local_user]
        # Command response mocking is easier without having to account for
        # shell wrapping everywhere.
        env.use_shell = False

    def teardown(self):
        env.update(self.previous_env)


def mock_streams(which):
    """
    Replaces a stream with a ``StringIO`` during the test, then restores after.

    Must specify which stream (stdout, stderr, etc) via string args, e.g.::

        @mock_streams('stdout')
        def func():
            pass

        @mock_streams('stderr')
        def func():
            pass

        @mock_streams('both')
        def func()
            pass
    """
    which = [which]
    if which == ['both']:
        which = ['stdout', 'stderr']
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


def password_response(password, times_called=None, silent=True):
    """
    Context manager which patches ``getpass.getpass`` to return ``password``.

    If ``times_called`` is given, it is used to add a ``Fake.times_called``
    clause to the mock object, e.g. ``.times_called(1)``.

    If ``silent`` is True, no prompt will be printed to ``sys.stderr``.
    """
    fake = Fake('getpass', callable=True).returns(password)
    if times_called:
        fake = fake.times_called(times_called)
    if not silent:
        fake = fake.calls(lambda x: sys.stderr.write(x))
    return patched_context(getpass, 'getpass', fake)


def assert_contains(needle, haystack):
    """
    Asserts ``haystack`` contains ``needle``.

    Raises with useful traceback/message, similar to nose/unittest.

    Turns on ``re.MULTILINE``.
    """
    if not re.search(needle, haystack, re.M):
        raise AssertionError("r'%s' not found in '%s'" % (
            needle,
            haystack
        ))
