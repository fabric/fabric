from __future__ import with_statement

import os
import sys

from nose.tools import eq_, ok_

from fabric.state import env, output
from fabric.context_managers import (cd, settings, lcd, hide, shell_env, quiet,
    warn_only, prefix, path)
from fabric.operations import run, local

from utils import mock_streams, FabricTest
from server import server
from StringIO import StringIO


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
#  prefix
#

def test_nested_prefix():
    """
    prefix context managers can be created outside of the with block and nested
    """
    cm1 = prefix('1')
    cm2 = prefix('2')
    with cm1:
        with cm2:
            eq_(env.command_prefixes, ['1', '2'])


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


#
# shell_env()
#

def test_shell_env():
    """
    shell_env() sets the shell_env attribute in the env dict
    """
    with shell_env(KEY="value"):
        eq_(env.shell_env['KEY'], 'value')

    eq_(env.shell_env, {})

class TestQuietAndWarnOnly(FabricTest):
    @server()
    @mock_streams('both')
    def test_quiet_hides_all_output(self):
        # Sanity test - normally this is not empty
        run("ls /simple")
        ok_(sys.stdout.getvalue())
        # Reset
        sys.stdout = StringIO()
        # Real test
        with quiet():
            run("ls /simple")
        # Empty output
        ok_(not sys.stdout.getvalue())
        # Reset
        sys.stdout = StringIO()
        # Kwarg test
        run("ls /simple", quiet=True)
        ok_(not sys.stdout.getvalue())

    @server(responses={'barf': [
        "this is my stdout",
        "this is my stderr",
        1
    ]})
    def test_quiet_sets_warn_only_to_true(self):
        # Sanity test to ensure environment
        with settings(warn_only=False):
            with quiet():
                eq_(run("barf").return_code, 1)
            # Kwarg test
            eq_(run("barf", quiet=True).return_code, 1)

    @server(responses={'hrm': ["", "", 1]})
    @mock_streams('both')
    def test_warn_only_is_same_as_settings_warn_only(self):
        with warn_only():
            eq_(run("hrm").failed, True)

    @server()
    @mock_streams('both')
    def test_warn_only_does_not_imply_hide_everything(self):
        with warn_only():
            run("ls /simple")
            assert sys.stdout.getvalue().strip() != ""


# path() (distinct from shell_env)

class TestPathManager(FabricTest):
    def setup(self):
        super(TestPathManager, self).setup()
        self.real = os.environ.get('PATH')

    def via_local(self):
        with hide('everything'):
            return local("echo $PATH", capture=True)

    def test_lack_of_path_has_default_local_path(self):
        """
        No use of 'with path' == default local $PATH
        """
        eq_(self.real, self.via_local())

    def test_use_of_path_appends_by_default(self):
        """
        'with path' appends by default
        """
        with path('foo'):
            eq_(self.via_local(), self.real + ":foo")
