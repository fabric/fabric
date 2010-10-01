from __future__ import with_statement

import os
j = os.path.join
import shutil
import sys
import tempfile

from nose.tools import raises, eq_
from fudge import with_patched_object

from fabric.state import env
from fabric.operations import require, prompt, _sudo_prefix, _shell_wrap, \
    _shell_escape
from fabric.api import get, put

from utils import *
from server import (server, PORT, RESPONSES, FILES, PASSWORDS, CLIENT_PRIVKEY,
    USER, CLIENT_PRIVKEY_PASSPHRASE)

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
# get() and put()
#

class TestFileTransfers(FabricTest):
    def setup(self):
        super(TestFileTransfers, self).setup()
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        super(TestFileTransfers, self).teardown()
        shutil.rmtree(self.tmpdir)

    @server()
    def test_get_single_file(self):
        remote = 'file.txt'
        get(self.tmpdir, remote)
        eq_(j(self.tmpdir, remote), FILES[remote].contents)
