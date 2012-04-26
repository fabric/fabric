from __future__ import with_statement

from nose.tools import eq_, ok_

from fabric.state import env, output
from fabric.context_managers import cd, settings, lcd, hide


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
    with settings(cwd=existing):
        with cd(absolute):
            eq_(env.cwd, absolute)
        with cd(additional):
            eq_(env.cwd, existing + '/' + additional)


#
# hide/show
#

def test_hide_show_exception_handling():
    """
    hide()/show() should clean up OK if exceptions are raised
    """
    try:
        with hide('stderr'):
            # now it's False, while the default is True
            eq_(output.stderr, False)
            raise Exception
    except Exception:
        # Here it should be True again.
        # If it's False, this means hide() didn't clean up OK.
        eq_(output.stderr, True)


#
# settings()
#

def test_setting_new_env_dict_key_should_work():
    """
    Using settings() with a previously nonexistent key should work correctly
    """
    key = 'thisshouldnevereverexistseriouslynow'
    value = 'a winner is you'
    with settings(**{key: value}):
        ok_(key in env)
    ok_(key not in env)


def test_settings():
    """
    settings() should temporarily override env dict with given key/value pair
    """
    env.testval = "outer value"
    with settings(testval="inner value"):
        eq_(env.testval, "inner value")
    eq_(env.testval, "outer value")

def test_settings_with_multiple_kwargs():
    """
    settings() should temporarily override env dict with given key/value pairS
    """
    env.testval1 = "outer 1"
    env.testval2 = "outer 2"
    with settings(testval1="inner 1", testval2="inner 2"):
        eq_(env.testval1, "inner 1")
        eq_(env.testval2, "inner 2")
    eq_(env.testval1, "outer 1")
    eq_(env.testval2, "outer 2")

def test_settings_with_other_context_managers():
    """
    settings() should take other context managers, and use them with other overrided
    key/value pairs.
    """
    env.testval1 = "outer 1"
    prev_lcwd = env.lcwd

    with settings(lcd("here"), testval1="inner 1"):
        eq_(env.testval1, "inner 1")
        ok_(env.lcwd.endswith("here")) # Should be the side-effect of adding cd to settings

    ok_(env.testval1, "outer 1")
    eq_(env.lcwd, prev_lcwd)


def test_settings_clean_revert():
    """
    settings(clean_revert=True) should only revert values matching input values
    """
    env.modified = "outer"
    env.notmodified = "outer"
    with settings(
        modified="inner",
        notmodified="inner",
        inner_only="only",
        clean_revert=True
    ):
        eq_(env.modified, "inner")
        eq_(env.notmodified, "inner")
        eq_(env.inner_only, "only")
        env.modified = "modified internally"
    eq_(env.modified, "modified internally")
    ok_("inner_only" not in env)
