from __future__ import with_statement

from nose.tools import eq_

from fabric.state import env
from fabric.context_managers import cd


#
# cd()
#

def test_error_handling():
    """
    cd cleans up after itself even in case of an exception
    """
    class TestException(Exception):
        pass
    try:
        with cd('somewhere'):
            raise TestException('Houston, we have a problem.')
    except TestException:
        pass
    finally:
        with cd('else'):
            eq_(env.cwd, 'else')


def test_cwd_with_absolute_paths():
    """
    cd() should append arg if non-absolute or overwrite otherwise
    """
    existing = '/some/existing/path' 
    additional = 'another'
    absolute = '/absolute/path'
    env.cwd = existing
    with cd(absolute):
        eq_(env.cwd, absolute)
    with cd(additional):
        eq_(env.cwd, existing + '/' + additional)
