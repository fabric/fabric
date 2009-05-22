from fudge.patcher import with_patched_object
from functools import wraps
from nose.tools import eq_

from nose.tools import raises
from fabric.state import output
from fabric.utils import warn, indent, abort
import sys
from StringIO import StringIO

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

@mock_streams('stderr')
@with_patched_object(output, 'warnings', True)
def test_warn():
    warn("Test")
    result = sys.stderr.getvalue()
    assert "\nWarning: Test\n\n" == result

def test_indent():
    for description, input, output in (
        ("Sanity check: 1 line string",
            'Test', '    Test'),
        ("List of strings turns in to strings joined by \n",
            ["Test", "Test"], '    Test\n    Test'),
    ):
        eq_.description = description
        yield eq_, indent(input), output
        del eq_.description

def test_indent_with_strip():
    for description, input, output in (
        ("Sanity check: 1 line string",
            indent('Test', strip=True), '    Test'),
        ("Check list of strings",
            indent(["Test", "Test"], strip=True), '    Test\n    Test'),
        ("Check list of strings",
            indent(["        Test", "        Test"], strip=True), '    Test\n    Test'),
    ):
        eq_.description = description
        yield eq_, input, output
        del eq_.description

@mock_streams('stderr')
@raises(SystemExit)
def test_abort():
    """
    Abort should raise SystemExit
    """
    abort("Test")

@mock_streams('stderr')
@with_patched_object(output, 'aborts', True)
def test_abort_message():
    try:
        abort("Test")
    except SystemExit:
        pass
    result = sys.stderr.getvalue()
    eq_("\nFatal error: Test\n\nAborting.\n", result)
   
