from __future__ import with_statement

from StringIO import StringIO # No need for cStringIO at this time
from contextlib import contextmanager
from functools import wraps, partial
from types import StringTypes
import copy
import getpass
import re
import sys

from fudge import Fake, patched_context, clear_expectations

from fabric.context_managers import settings
from fabric.network import interpret_host_string
from fabric.state import env, output
import fabric.network

from server import PORT, PASSWORDS, USER, HOST


class FabricTest(object):
    """
    Nose-oriented test runner class that wipes env after every test.
    """
    def setup(self):
        # Clear Fudge mock expectations
        clear_expectations()
        # Copy env, output for restoration in teardown
        self.previous_env = copy.deepcopy(env)
        # Deepcopy doesn't work well on AliasDicts; but they're only one layer
        # deep anyways, so...
        self.previous_output = output.items()
        # Set up default networking for test server
        env.disable_known_hosts = True
        interpret_host_string('%s@%s:%s' % (USER, HOST, PORT))
        env.password = PASSWORDS[USER]
        # Command response mocking is easier without having to account for
        # shell wrapping everywhere.
        env.use_shell = False

    def teardown(self):
        env.update(self.previous_env)
        output.update(self.previous_output)


class CarbonCopy(StringIO):
    """
    A StringIO capable of multiplexing its writes to other buffer objects.
    """

    def __init__(self, buffer='', cc=None):
        """
        If ``cc`` is given and is a file-like object or an iterable of same,
        it/they will be written to whenever this StringIO instance is written
        to.
        """
        StringIO.__init__(self, buffer)
        if cc is None:
            cc = []
        elif hasattr(cc, 'write'):
            cc = [cc]
        self.cc = cc

    def write(self, s):
        StringIO.write(self, s)
        for writer in self.cc:
            writer.write(s)


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

    If ``'both'`` is specified, not only will both streams be replaced with
    StringIOs, but a new combined-streams output (another StringIO) will appear
    at ``sys.stdall``. This StringIO will resemble what a user sees at a
    terminal, i.e. both streams intermingled.
    """
    both = (which == 'both')
    stdout = (which == 'stdout') or both
    stderr = (which == 'stderr') or both
    def mocked_streams_decorator(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            if both:
                sys.stdall = StringIO()
                fake_stdout = CarbonCopy(cc=sys.stdall)
                fake_stderr = CarbonCopy(cc=sys.stdall)
            else:
                fake_stdout, fake_stderr = StringIO(), StringIO()
            if stdout:
                my_stdout, sys.stdout = sys.stdout, fake_stdout
            if stderr:
                my_stderr, sys.stderr = sys.stderr, fake_stderr
            try:
                ret = func(*args, **kwargs)
            finally:
                if stdout:
                    sys.stdout = my_stdout
                if stderr:
                    sys.stderr = my_stderr
                if both:
                    del sys.stdall
        return inner_wrapper
    return mocked_streams_decorator


def password_response(password, times_called=None, silent=True):
    """
    Context manager which patches ``getpass.getpass`` to return ``password``.

    ``password`` may be a single string or an iterable of strings:

    * If single string, given password is returned every time ``getpass`` is
      called.
    * If iterable, iterated over for each call to ``getpass``, after which
      ``getpass`` will error.

    If ``times_called`` is given, it is used to add a ``Fake.times_called``
    clause to the mock object, e.g. ``.times_called(1)``. Specifying
    ``times_called`` alongside an iterable ``password`` list is unsupported
    (see Fudge docs on ``Fake.next_call``).

    If ``silent`` is True, no prompt will be printed to ``sys.stderr``.
    """
    fake = Fake('getpass', callable=True)
    # Assume stringtype or iterable, turn into mutable iterable
    if isinstance(password, StringTypes):
        passwords = [password]
    else:
        passwords = list(password)
    # Optional echoing of prompt to mimic real behavior of getpass
    # NOTE: also echo a newline if the prompt isn't a "passthrough" from the
    # server (as it means the server won't be sending its own newline for us).
    echo = lambda x, y: y.write(x + ("\n" if x != " " else ""))
    # Always return first (only?) password right away
    fake = fake.returns(passwords.pop(0))
    if not silent:
        fake = fake.calls(echo)
    # If we had >1, return those afterwards
    for pw in passwords:
        fake = fake.next_call().returns(pw)
        if not silent:
            fake = fake.calls(echo)
    # Passthrough times_called
    if times_called:
        fake = fake.times_called(times_called)
    return patched_context(getpass, 'getpass', fake)


def _assert_contains(needle, haystack, invert):
    matched = re.search(needle, haystack, re.M)
    if (invert and matched) or (not invert and not matched):
        raise AssertionError("r'%s' %sfound in '%s'" % (
            needle,
            "" if invert else "not ",
            haystack
        ))

assert_contains = partial(_assert_contains, invert=False)
assert_not_contains = partial(_assert_contains, invert=True)


def line_prefix(prefix, string):
    """
    Return ``string`` with all lines prefixed by ``prefix``.
    """
    return "\n".join(prefix + x for x in string.splitlines())


def eq_(a, b, msg=None):
    """
    Shadow of the Nose builtin which presents easier to read multiline output.
    """
    default_msg = """
Expected:
%s

Got:
%s

--------------------------------- aka -----------------------------------------

Expected:
%r

Got:
%r
""" % (a, b, a, b)
    assert a == b, msg or default_msg


def eq_contents(path, text):
    with open(path) as fd:
        eq_(text, fd.read())
