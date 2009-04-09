from __future__ import with_statement
from functools import wraps
from StringIO import StringIO # No need for cStringIO at this time
import sys

from nose.tools import raises

from fabric.operations import require
from fabric.state import env


#
# Setup/teardown helpers and decorators
#

def mock_streams(*which):
    """
    Replaces ``sys.stderr`` with a ``StringIO`` during the test, then restores
    after.

    Must specify which stream via string args, e.g.::

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



#
# require()
#

def test_require_single_existing_key():
    """
    When given a single existing key, require() throws no exceptions
    """
    # 'version' is one of the default values, so we know it'll be there
    require('version')


def test_require_multiple_existing_keys():
    """
    When given multiple existing keys, require() throws no exceptions
    """
    require('version', 'settings_file')


@mock_streams('stderr')
@raises(SystemExit)
def test_require_single_missing_key():
    """
    When given a single non-existent key, require() raises SystemExit
    """
    require('blah')


@mock_streams('stderr')
@raises(SystemExit)
def test_require_multiple_missing_keys():
    """
    When given multiple non-existent keys, require() raises SystemExit
    """
    require('foo', 'bar')


@mock_streams('stderr')
@raises(SystemExit)
def test_require_mixed_state_keys():
    """
    When given mixed-state keys, require() raises SystemExit
    """
    require('foo', 'version')


@mock_streams('stderr')
def test_require_mixed_state_keys_prints_missing_only():
    """
    When given mixed-state keys, require() prints missing keys only
    """
    try:
        require('foo', 'version')
    except SystemExit:
        err = sys.stderr.getvalue()
        assert 'version' not in err
        assert 'foo' in err
