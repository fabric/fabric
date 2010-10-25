from __future__ import with_statement

import os
import shutil
import sys
import tempfile

from nose.tools import raises, eq_
from fudge import with_patched_object

from fabric.state import env
from fabric.operations import require, prompt, _sudo_prefix, _shell_wrap, \
    _shell_escape
from fabric.api import get, put, hide

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

    def path(self, *path_parts):
        return os.path.join(self.tmpdir, *path_parts)

    #
    # get()
    #

    @server()
    def test_get_single_file(self):
        """
        get() with a single non-globbed filename
        """
        remote = 'file.txt'
        local = self.path(remote)
        with hide('everything'):
            get(remote, local)
        eq_contents(local, FILES[remote])


    @server()
    def test_get_sibling_globs(self):
        """
        get() with globbed files, but no directories
        """
        remotes = ['file.txt', 'file2.txt']
        with hide('everything'):
            get('file*.txt', self.tmpdir)
        for remote in remotes:
            eq_contents(self.path(remote), FILES[remote])


    @server()
    def test_get_single_file_recursively(self):
        """
        Recursively get() a folder containing one file
        """
        remote = 'folder/file3.txt'
        with hide('everything'):
            get('folder', self.tmpdir, recursive=True)
        eq_contents(self.path(remote), FILES[remote])


    @server()
    @mock_streams('both')
    def test_get_folder_non_recursively(self):
        """
        get(folder, recursive=False) should warn and skip
        """
        target = 'folder'
        remote = 'folder/file3.txt'
        get(target, self.tmpdir)
        assert ("%s is a directory" % target) in sys.stderr.getvalue()
        assert not os.path.exists(self.path(target))


    @server()
    def test_get_tree_recursively(self):
        """
        Download entire tree, recursively
        """
        with hide('everything'):
            get('tree', self.tmpdir, recursive=True)
        leaves = filter(lambda x: x[0].startswith('tree'), FILES.items())
        for path, contents in leaves:
            eq_contents(self.path(path), contents)


    @server()
    def test_get_single_file_absolutely(self):
        """
        get() a single file, using absolute file path
        """
        target = '/etc/apache2/apache2.conf'
        with hide('everything'):
            get(target, self.tmpdir)
        eq_contents(self.path(os.path.basename(target)), FILES[target])


    @server()
    def test_get_file_with_nonexistent_target(self):
        """
        Missing target path on single file download => effectively a rename
        """
        local = self.path('otherfile.txt')
        target = 'file.txt'
        with hide('everything'):
            get(target, local)
        eq_contents(local, FILES[target])


    @server()
    @mock_streams('stderr')
    def test_get_file_with_existing_file_target(self):
        """
        Clobbering existing local file should overwrite, with warning
        """
        local = self.path('target.txt')
        target = 'file.txt'
        with open(local, 'w') as fd:
            fd.write("foo")
        with hide('stdout', 'running'):
            get(target, local)
        assert "%s already exists" % local in sys.stderr.getvalue()
        eq_contents(local, FILES[target])


    @server()
    def test_get_file_to_directory(self):
        """
        Directory as target path should result in joined pathname

        (Yes, this is duplicated in most of the other tests -- but good to have
        a default in case those tests change how they work later!)
        """
        target = 'file.txt'
        with hide('everything'):
            get(target, self.tmpdir)
        eq_contents(self.path(target), FILES[target])

#
#    @server()
#    def test_get_files_from_multiple_servers(self):
#        """
#        Hopefully two @server uses with different ports will work as expected
#        """
#        assert False
#
#
    @server()
    def test_get_from_empty_directory_uses_cwd(self):
        """
        get() expands empty remote arg to remote cwd
        """
        with hide('everything'):
            get('', self.tmpdir, recursive=True)
        # Spot checks
        for x in "file.txt file2.txt tree/file1.txt".split():
            assert os.path.exists(os.path.join(self.tmpdir, x))


    @server()
    def test_get_to_empty_directory_uses_cwd(self):
        """
        get() expands empty local arg to local cwd
        """
        path = 'file.txt'
        with hide('everything'):
            get(path, '')
        target = os.path.join(os.getcwd(), path)
        assert os.path.exists(target)
        # Clean up, since we're not using our tmpdir
        os.remove(target)


    #
    # put()
    #

    @server()
    def test_put_file_to_existing_directory(self):
        """
        put() a single file into an existing remote directory
        """
        local = self.path('foo.txt')
        local2 = self.path('foo2.txt')
        with open(local, 'w') as fd:
            fd.write("foo!")
        with hide('everything'):
            put(local, '/')
            get('/foo.txt', local2)
        eq_contents(local2, "foo!")


    @server()
    def test_put_to_empty_directory_uses_cwd(self):
        """
        put() expands empty remote arg to remote cwd
        """
        assert False


    @server()
    def test_put_from_empty_directory_uses_cwd(self):
        """
        put() expands empty local arg to local cwd
        """
        assert False
