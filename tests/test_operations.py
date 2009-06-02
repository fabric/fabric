from __future__ import with_statement

import sys

from nose.tools import raises, eq_
from fudge import with_patched_object

from fabric.operations import require, prompt
from utils import mock_streams


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
    require('version', 'sudo_prompt')


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


#
# prompt()
#

def p(x):
    print x,

@mock_streams('stdout')
@with_patched_object(sys.modules['__builtin__'], 'raw_input', p)
def test_prompt_appends_space():
    """
    prompt() appends a single space when no default is given
    """
    s = "This is my prompt"
    prompt(s)
    eq_(sys.stdout.getvalue(), s + ' ')


@mock_streams('stdout')
@with_patched_object(sys.modules['__builtin__'], 'raw_input', p)
def test_prompt_with_default():
    """
    prompt() appends given default value plus one space on either side
    """
    s = "This is my prompt"
    d = "default!"
    prompt(s, default=d)
    eq_(sys.stdout.getvalue(), "%s [%s] " % (s, d))
