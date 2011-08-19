from __future__ import with_statement

import sys

from fudge import Fake, patched_context, verify, clear_expectations
from fudge.patcher import with_patched_object
from nose.tools import eq_
from nose.tools import raises

from fabric.state import output, env
from fabric.utils import warn, indent, abort, puts, fastprint, human_readable_size
from fabric import utils  # For patching
from fabric.context_managers import settings
from utils import mock_streams


@mock_streams('stderr')
@with_patched_object(output, 'warnings', True)
def test_warn():
    """
    warn() should print 'Warning' plus given text
    """
    warn("Test")
    assert "\nWarning: Test\n\n" == sys.stderr.getvalue()


def test_indent():
    for description, input, output in (
        ("Sanity check: 1 line string",
            'Test', '    Test'),
        ("List of strings turns in to strings joined by \\n",
            ["Test", "Test"], '    Test\n    Test'),
    ):
        eq_.description = "indent(): %s" % description
        yield eq_, indent(input), output
        del eq_.description


def test_indent_with_strip():
    for description, input, output in (
        ("Sanity check: 1 line string",
            indent('Test', strip=True), '    Test'),
        ("Check list of strings",
            indent(["Test", "Test"], strip=True), '    Test\n    Test'),
        ("Check list of strings",
            indent(["        Test", "        Test"], strip=True),
            '    Test\n    Test'),
    ):
        eq_.description = "indent(strip=True): %s" % description
        yield eq_, input, output
        del eq_.description


@mock_streams('stderr')
@raises(SystemExit)
def test_abort():
    """
    abort() should raise SystemExit
    """
    abort("Test")


@mock_streams('stderr')
@with_patched_object(output, 'aborts', True)
def test_abort_message():
    """
    abort() should print 'Fatal error' plus exception value
    """
    try:
        abort("Test")
    except SystemExit:
        pass
    result = sys.stderr.getvalue()
    eq_("\nFatal error: Test\n\nAborting.\n", result)


@mock_streams('stdout')
def test_puts_with_user_output_on():
    """
    puts() should print input to sys.stdout if "user" output level is on
    """
    s = "string!"
    output.user = True
    puts(s, show_prefix=False)
    eq_(sys.stdout.getvalue(), s + "\n")


@mock_streams('stdout')
def test_puts_with_user_output_off():
    """
    puts() shouldn't print input to sys.stdout if "user" output level is off
    """
    output.user = False
    puts("You aren't reading this.")
    eq_(sys.stdout.getvalue(), "")


@mock_streams('stdout')
def test_puts_with_prefix():
    """
    puts() should prefix output with env.host_string if non-empty
    """
    s = "my output"
    h = "localhost"
    with settings(host_string=h):
        puts(s)
    eq_(sys.stdout.getvalue(), "[%s] %s" % (h, s + "\n"))


@mock_streams('stdout')
def test_puts_without_prefix():
    """
    puts() shouldn't prefix output with env.host_string if show_prefix is False
    """
    s = "my output"
    h = "localhost"
    puts(s, show_prefix=False)
    eq_(sys.stdout.getvalue(), "%s" % (s + "\n"))


def test_fastprint_calls_puts():
    """
    fastprint() is just an alias to puts()
    """
    text = "Some output"
    fake_puts = Fake('puts', expect_call=True).with_args(
        text=text, show_prefix=False, end="", flush=True
    )
    with patched_context(utils, 'puts', fake_puts):
        try:
            fastprint(text)
            verify()
        finally:
            clear_expectations()


def test_human_readable_size():
    """ Testing return of human_readable_size """

    assert human_readable_size(10) == '10 B'
    assert human_readable_size(1024) == '1.00 kiB'
    assert human_readable_size(1024 + 512) == '1.50 kiB'
    assert human_readable_size(1024 ** 2) == '1.00 MiB'
    assert human_readable_size(1024 ** 3) == '1.00 GiB'
    assert human_readable_size(1024 ** 4) == '1.00 TiB'
    assert human_readable_size(1024 ** 5) == '1.00 PiB'

