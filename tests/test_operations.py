from nose.tools import raises

from fabric.operations import require
from fabric.state import env


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


@raises(StandardError)
def test_require_single_missing_key():
    """
    When given a single non-existent key, require() raises StandardError
    """
    require('blah')


@raises(StandardError)
def test_require_multiple_missing_keys():
    """
    When given multiple non-existent keys, require() raises StandardError
    """
    require('foo', 'bar')


@raises(StandardError)
def test_require_mixed_state_keys():
    """
    When given existing and non-existent keys, require() raises StandardError
    """
    require('foo', 'version')
