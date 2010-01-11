from __future__ import with_statement

import sys

import unittest
import random
import types

from nose.tools import raises, eq_
from fudge import with_patched_object

from fabric.state import env
from fabric.operations import require, prompt, _sudo_prefix, _shell_wrap, \
    _shell_escape, do
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
    

#
# run()/sudo()
#

def test_sudo_prefix_with_user():
    """
    _sudo_prefix() returns prefix plus -u flag for nonempty user
    """
    eq_(
        _sudo_prefix(user="foo"),
        "%s -u \"foo\" " % (env.sudo_prefix % env.sudo_prompt)
    )


def test_sudo_prefix_without_user():
    """
    _sudo_prefix() returns standard prefix when user is empty
    """
    eq_(_sudo_prefix(user=None), env.sudo_prefix % env.sudo_prompt)


def test_shell_wrap():
    prefix = "prefix"
    command = "command"
    for description, shell, sudo_prefix, result in (
        ("shell=True, sudo_prefix=None",
            True, None, "%s \"%s\"" % (env.shell, command)),
        ("shell=True, sudo_prefix=string",
            True, prefix, prefix + " %s \"%s\"" % (env.shell, command)),
        ("shell=False, sudo_prefix=None",
            False, None, command),
        ("shell=False, sudo_prefix=string",
            False, prefix, prefix + " " + command),
    ):
        eq_.description = "_shell_wrap: %s" % description
        yield eq_, _shell_wrap(command, shell, sudo_prefix), result
        del eq_.description


def test_shell_wrap_escapes_command_if_shell_is_true():
    """
    _shell_wrap() escapes given command if shell=True
    """
    cmd = "cd \"Application Support\""
    eq_(
        _shell_wrap(cmd, shell=True),
        '%s "%s"' % (env.shell, _shell_escape(cmd))
    )


def test_shell_wrap_does_not_escape_command_if_shell_is_false():
    """
    _shell_wrap() does no escaping if shell=False
    """
    cmd = "cd \"Application Support\""
    eq_(_shell_wrap(cmd, shell=False), cmd)


def test_shell_escape_escapes_doublequotes():
    """
    _shell_escape() escapes double-quotes
    """
    cmd = "cd \"Application Support\""
    eq_(_shell_escape(cmd), 'cd \\"Application Support\\"')


def test_shell_escape_escapes_dollar_signs():
    """
    _shell_escape() escapes dollar signs
    """
    cmd = "cd $HOME"
    eq_(_shell_escape(cmd), 'cd \$HOME')


def test_shell_escape_escapes_backticks():
    """
    _shell_escape() escapes backticks
    """
    cmd = "touch test.pid && kill `cat test.pid`"
    eq_(_shell_escape(cmd), "touch test.pid && kill \`cat test.pid\`")


#
# do()
#
class MockCommand(object):
    def __init__(self):
        self.args = None
        self.kwargs = None

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class TestOfDoOperation(unittest.TestCase):
    def setUp(self):
        self.replace_operations()

    def tearDown(self):
        self.restore_operations()

    def replace_operations(self):
        operations = sys.modules['fabric.operations']
        self.original_run = operations.run
        self.original_local = operations.local
        self.original_sudo = operations.sudo
        self.mock_run = operations.run = MockCommand()
        self.mock_local = operations.local = MockCommand()
        self.mock_sudo = operations.sudo = MockCommand()

    def restore_operations(self):
        operations = sys.modules['fabric.operations']
        operations.run = self.original_run
        operations.local = self.original_local
        operations.sudo = self.original_sudo

    def remove_run_as_if_present(self):
        if hasattr(env, "run_as"):
            del env['run_as']

    def random_ls(self):
        random_string = ("foo*", "bar*", "baz*")[random.randint(0, 2)]
        return "ls -l %s" % random_string

    def assertNone(self, a):
        self.assertEqual(types.NoneType, type(a))

    def test_run_called_on_remote_do(self):
        env['run_as'] = "remote"
        cmd = self.random_ls()
        do(cmd)
        self.assertEqual(types.TupleType, type(self.mock_run.args))
        self.assert_(cmd in self.mock_run.args)
        self.assertEqual(types.NoneType, type(self.mock_local.args))

    def test_local_called_on_local_do(self):
        env['run_as'] = "local"
        cmd = self.random_ls()
        do(cmd)
        self.assertEqual(types.TupleType, type(self.mock_local.args))
        self.assert_(cmd in self.mock_local.args)
        self.assertEqual(types.NoneType, type(self.mock_run.args))

    def test_defaults_to_run_in_the_presence_of_no_run_as(self):
        self.remove_run_as_if_present()
        cmd = self.random_ls()
        do(cmd)
        self.assertEqual(types.TupleType, type(self.mock_run.args))
        self.assert_(cmd in self.mock_run.args)
        self.assertEqual(types.NoneType, type(self.mock_local.args))

    def test_sudo_called_on_remote_do_with_sudo_kwarg_set_to_true(self):
        env['run_as'] = 'remote'
        cmd = self.random_ls()
        do(cmd, sudo=True)
        self.assertNone(self.mock_run.args)
        self.assertNone(self.mock_local.args)
        self.assert_(cmd in self.mock_sudo.args)
        self.assert_("sudo" not in self.mock_sudo.kwargs)

if __name__ == "__main__":
    unittest.main()
