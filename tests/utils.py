from __future__ import with_statement

from contextlib import contextmanager
from copy import deepcopy
from fudge.patcher import with_patched_object
from functools import partial
from types import StringTypes
import copy
import getpass
import os
import re
import shutil
import sys
import tempfile

from fudge import Fake, patched_context, clear_expectations, with_patched_object
from nose.tools import raises
from nose import SkipTest

from fabric.context_managers import settings
from fabric.state import env, output
from fabric.sftp import SFTP
import fabric.network
from fabric.network import normalize, to_dict

from server import PORT, PASSWORDS, USER, HOST
from mock_streams import mock_streams


class FabricTest(object):
    """
    Nose-oriented test runner which wipes state.env and provides file helpers.
    """
    def setup(self):
        # Clear Fudge mock expectations
        clear_expectations()
        # Copy env, output for restoration in teardown
        self.previous_env = copy.deepcopy(env)
        # Deepcopy doesn't work well on AliasDicts; but they're only one layer
        # deep anyways, so...
        self.previous_output = output.items()
        # Allow hooks from subclasses here for setting env vars (so they get
        # purged correctly in teardown())
        self.env_setup()
        # Temporary local file dir
        self.tmpdir = tempfile.mkdtemp()

    def set_network(self):
        env.update(to_dict('%s@%s:%s' % (USER, HOST, PORT)))

    def env_setup(self):
        # Set up default networking for test server
        env.disable_known_hosts = True
        self.set_network()
        env.password = PASSWORDS[USER]
        # Command response mocking is easier without having to account for
        # shell wrapping everywhere.
        env.use_shell = False

    def teardown(self):
        env.clear() # In case tests set env vars that didn't exist previously
        env.update(self.previous_env)
        output.update(self.previous_output)
        shutil.rmtree(self.tmpdir)
        # Clear Fudge mock expectations...again
        clear_expectations()

    def path(self, *path_parts):
        return os.path.join(self.tmpdir, *path_parts)

    def mkfile(self, path, contents):
        dest = self.path(path)
        with open(dest, 'w') as fd:
            fd.write(contents)
        return dest

    def exists_remotely(self, path):
        return SFTP(env.host_string).exists(path)

    def exists_locally(self, path):
        return os.path.exists(path)


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


def eq_(result, expected, msg=None):
    """
    Shadow of the Nose builtin which presents easier to read multiline output.
    """
    params = {'expected': expected, 'result': result}
    aka = """

--------------------------------- aka -----------------------------------------

Expected:
%(expected)r

Got:
%(result)r
""" % params
    default_msg = """
Expected:
%(expected)s

Got:
%(result)s
""" % params
    if (repr(result) != str(result)) or (repr(expected) != str(expected)):
        default_msg += aka
    assert result == expected, msg or default_msg


def eq_contents(path, text):
    with open(path) as fd:
        eq_(text, fd.read())


def support(path):
    return os.path.join(os.path.dirname(__file__), 'support', path)

fabfile = support


@contextmanager
def path_prefix(module):
    i = 0
    sys.path.insert(i, os.path.dirname(module))
    yield
    sys.path.pop(i)


def aborts(func):
    return raises(SystemExit)(mock_streams('stderr')(func))


def _patched_input(func, fake):
    return func(sys.modules['__builtin__'], 'raw_input', fake)
patched_input = partial(_patched_input, patched_context)
with_patched_input = partial(_patched_input, with_patched_object)
