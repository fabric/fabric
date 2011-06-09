from __future__ import with_statement

import os
import shutil
import sys
import types
from contextlib import nested
from StringIO import StringIO

import unittest
import random
import types

from nose.tools import raises, eq_
from fudge import with_patched_object

from fabric.state import env, output
from fabric.operations import require, prompt, _sudo_prefix, _shell_wrap, \
    _shell_escape
from fabric.api import get, put, hide, show, cd, lcd, local, run, sudo
from fabric.sftp import SFTP

from fabric.decorators import with_settings
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


@mock_streams('stderr')
@raises(SystemExit)
def test_require_iterable_provided_by_key():
    """
    When given a provided_by iterable value, require() raises SystemExit
    """
    # 'version' is one of the default values, so we know it'll be there
    def fake_providing_function():
        pass
    require('foo', provided_by=[fake_providing_function])


@mock_streams('stderr')
@raises(SystemExit)
def test_require_noniterable_provided_by_key():
    """
    When given a provided_by noniterable value, require() raises SystemExit
    """
    # 'version' is one of the default values, so we know it'll be there
    def fake_providing_function():
        pass
    require('foo', provided_by=fake_providing_function)


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


@with_settings(use_shell=True)
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


@with_settings(use_shell=True)
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


class TestCombineStderr(FabricTest):
    @server()
    def test_local_none_global_true(self):
        """
        combine_stderr: no kwarg => uses global value (True)
        """
        output.everything = False
        r = run("both_streams")
        # Note: the exact way the streams are jumbled here is an implementation
        # detail of our fake SSH server and may change in the future.
        eq_("ssttddoeurtr", r.stdout)
        eq_(r.stderr, "")

    @server()
    def test_local_none_global_false(self):
        """
        combine_stderr: no kwarg => uses global value (False)
        """
        output.everything = False
        env.combine_stderr = False
        r = run("both_streams")
        eq_("stdout", r.stdout)
        eq_("stderr", r.stderr)

    @server()
    def test_local_true_global_false(self):
        """
        combine_stderr: True kwarg => overrides global False value
        """
        output.everything = False
        env.combine_stderr = False
        r = run("both_streams", combine_stderr=True)
        eq_("ssttddoeurtr", r.stdout)
        eq_(r.stderr, "")

    @server()
    def test_local_false_global_true(self):
        """
        combine_stderr: False kwarg => overrides global True value
        """
        output.everything = False
        env.combine_stderr = True
        r = run("both_streams", combine_stderr=False)
        eq_("stdout", r.stdout)
        eq_("stderr", r.stderr)

#
# get() and put()
#

class TestFileTransfers(FabricTest):
    #
    # get()
    #
    @server(files={'/home/user/.bashrc': 'bash!'}, home='/home/user')
    def test_get_relative_remote_dir_uses_home(self):
        """
        get('relative/path') should use remote $HOME
        """
        with hide('everything'):
            # Another if-it-doesn't-error-out-it-passed test; meh.
            eq_(get('.bashrc', self.path()), [self.path('.bashrc')])

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
    def test_get_single_file_in_folder(self):
        """
        get() a folder containing one file
        """
        remote = 'folder/file3.txt'
        with hide('everything'):
            get('folder', self.tmpdir)
        eq_contents(self.path(remote), FILES[remote])

    @server()
    def test_get_tree(self):
        """
        Download entire tree
        """
        with hide('everything'):
            get('tree', self.tmpdir)
        leaves = filter(lambda x: x[0].startswith('/tree'), FILES.items())
        for path, contents in leaves:
            eq_contents(self.path(path[1:]), contents)

    @server()
    def test_get_tree_with_implicit_local_path(self):
        """
        Download entire tree without specifying a local path
        """
        dirname = env.host_string.replace(':', '-')
        try:
            with hide('everything'):
                get('tree')
            leaves = filter(lambda x: x[0].startswith('/tree'), FILES.items())
            for path, contents in leaves:
                path = os.path.join(dirname, path[1:])
                eq_contents(path, contents)
                os.remove(path)
        # Cleanup
        finally:
            if os.path.exists(dirname):
                shutil.rmtree(dirname)

    @server()
    def test_get_absolute_path_should_save_relative(self):
        """
        get(/x/y) w/ %(path)s should save y, not x/y
        """
        lpath = self.path()
        ltarget = os.path.join(lpath, "%(path)s")
        with hide('everything'):
            get('/tree/subfolder', ltarget)
        assert self.exists_locally(os.path.join(lpath, 'subfolder'))
        assert not self.exists_locally(os.path.join(lpath, 'tree/subfolder'))

    @server()
    def test_path_formatstr_nonrecursively_is_just_filename(self):
        """
        get(x/y/z) nonrecursively w/ %(path)s should save y, not y/z
        """
        lpath = self.path()
        ltarget = os.path.join(lpath, "%(path)s")
        with hide('everything'):
            get('/tree/subfolder/file3.txt', ltarget)
        assert self.exists_locally(os.path.join(lpath, 'file3.txt'))

    @server()
    @mock_streams('stderr')
    def _invalid_file_obj_situations(self, remote_path):
        with settings(hide('running'), warn_only=True):
            get(remote_path, StringIO())
        assert_contains('is a glob or directory', sys.stderr.getvalue())

    def test_glob_and_file_object_invalid(self):
        """
        Remote glob and local file object is invalid
        """
        self._invalid_file_obj_situations('/tree/*')

    def test_directory_and_file_object_invalid(self):
        """
        Remote directory and local file object is invalid
        """
        self._invalid_file_obj_situations('/tree')

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

    @server(port=2200)
    @server(port=2201)
    def test_get_from_multiple_servers(self):
        ports = [2200, 2201]
        hosts = map(lambda x: '127.0.0.1:%s' % x, ports)
        with settings(all_hosts=hosts):
            for port in ports:
                with settings(
                    hide('everything'), host_string='127.0.0.1:%s' % port
                ):
                    tmp = self.path('')
                    local_path = os.path.join(tmp, "%(host)s", "%(path)s")
                    # Top level file
                    path = 'file.txt'
                    get(path, local_path)
                    assert self.exists_locally(os.path.join(
                        tmp, "127.0.0.1-%s" % port, path
                    ))
                    # Nested file
                    get('tree/subfolder/file3.txt', local_path)
                    assert self.exists_locally(os.path.join(
                        tmp, "127.0.0.1-%s" % port, 'file3.txt'
                    ))

    @server()
    def test_get_from_empty_directory_uses_cwd(self):
        """
        get() expands empty remote arg to remote cwd
        """
        with hide('everything'):
            get('', self.tmpdir)
        # Spot checks -- though it should've downloaded the entirety of
        # server.FILES.
        for x in "file.txt file2.txt tree/file1.txt".split():
            assert os.path.exists(os.path.join(self.tmpdir, x))

    @server()
    def _get_to_cwd(self, arg):
        path = 'file.txt'
        with hide('everything'):
            get(path, arg)
        host_dir = os.path.join(
            os.getcwd(),
            env.host_string.replace(':', '-'),
        )
        target = os.path.join(host_dir, path)
        try:
            assert os.path.exists(target)
        # Clean up, since we're not using our tmpdir
        finally:
            shutil.rmtree(host_dir)

    def test_get_to_empty_string_uses_default_format_string(self):
        """
        get() expands empty local arg to local cwd + host + file
        """
        self._get_to_cwd('')

    def test_get_to_None_uses_default_format_string(self):
        """
        get() expands None local arg to local cwd + host + file
        """
        self._get_to_cwd(None)

    @server()
    def test_get_should_accept_file_like_objects(self):
        """
        get()'s local_path arg should take file-like objects too
        """
        fake_file = StringIO()
        target = '/file.txt'
        with hide('everything'):
            get(target, fake_file)
        eq_(fake_file.getvalue(), FILES[target])

    @server()
    def test_get_interpolation_without_host(self):
        """
        local formatting should work w/o use of %(host)s when run on one host
        """
        with hide('everything'):
            tmp = self.path('')
            # dirname, basename
            local_path = tmp + "/%(dirname)s/foo/%(basename)s"
            get('/folder/file3.txt', local_path)
            assert self.exists_locally(tmp + "foo/file3.txt")
            # path
            local_path = tmp + "bar/%(path)s"
            get('/folder/file3.txt', local_path)
            assert self.exists_locally(tmp + "bar/file3.txt")

    @server()
    def test_get_returns_list_of_local_paths(self):
        """
        get() should return an iterable of the local files it created.
        """
        d = self.path()
        with hide('everything'):
            retval = get('tree', d)
        files = ['file1.txt', 'file2.txt', 'subfolder/file3.txt']
        eq_(map(lambda x: os.path.join(d, 'tree', x), files), retval)

    @server()
    def test_get_returns_none_for_stringio(self):
        """
        get() should return None if local_path is a StringIO
        """
        with hide('everything'):
            eq_([], get('/file.txt', StringIO()))

    @server()
    def test_get_return_value_failed_attribute(self):
        """
        get()'s return value should indicate any paths which failed to
        download.
        """
        with settings(hide('everything'), warn_only=True):
            retval = get('/doesnt/exist', self.path())
        eq_(['/doesnt/exist'], retval.failed)
        assert not retval.succeeded

    @server()
    def test_get_should_not_use_windows_slashes_in_remote_paths(self):
        """
        sftp.glob() should always use Unix-style slashes.
        """
        with hide('everything'):
            path = "/tree/file1.txt"
            sftp = SFTP(env.host_string)
            eq_(sftp.glob(path), [path])

    #
    # put()
    #
    @server()
    def test_put_file_to_existing_directory(self):
        """
        put() a single file into an existing remote directory
        """
        text = "foo!"
        local = self.mkfile('foo.txt', text)
        local2 = self.path('foo2.txt')
        with hide('everything'):
            put(local, '/')
            get('/foo.txt', local2)
        eq_contents(local2, text)

    @server()
    def test_put_to_empty_directory_uses_cwd(self):
        """
        put() expands empty remote arg to remote cwd

        Not a terribly sharp test -- we just get() with a relative path and are
        testing to make sure they match up -- but should still suffice.
        """
        text = "foo!"
        local = self.path('foo.txt')
        local2 = self.path('foo2.txt')
        with open(local, 'w') as fd:
            fd.write(text)
        with hide('everything'):
            put(local)
            get('foo.txt', local2)
        eq_contents(local2, text)

    @server()
    def test_put_from_empty_directory_uses_cwd(self):
        """
        put() expands empty local arg to local cwd
        """
        text = 'foo!'
        # Don't use the current cwd since that's a whole lotta files to upload
        old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        # Write out file right here
        with open('file.txt', 'w') as fd:
            fd.write(text)
        with hide('everything'):
            # Put our cwd (which should only contain the file we just created)
            put('', '/')
            # Get it back under a new name (noting that when we use a truly
            # empty put() local call, it makes a directory remotely with the
            # name of the cwd)
            remote = os.path.join(os.path.basename(self.tmpdir), 'file.txt')
            get(remote, 'file2.txt')
        # Compare for sanity test
        eq_contents('file2.txt', text)
        # Restore cwd
        os.chdir(old_cwd)

    @server()
    def test_put_should_accept_file_like_objects(self):
        """
        put()'s local_path arg should take file-like objects too
        """
        local = self.path('whatever')
        fake_file = StringIO()
        fake_file.write("testing file-like objects in put()")
        pointer = fake_file.tell()
        target = '/new_file.txt'
        with hide('everything'):
            put(fake_file, target)
            get(target, local)
        eq_contents(local, fake_file.getvalue())
        # Sanity test of file pointer
        eq_(pointer, fake_file.tell())

    @server()
    @raises(ValueError)
    def test_put_should_raise_exception_for_nonexistent_local_path(self):
        """
        put(nonexistent_file) should raise a ValueError
        """
        put('thisfiledoesnotexist', '/tmp')

    @server()
    def test_put_returns_list_of_remote_paths(self):
        """
        put() should return an iterable of the remote files it created.
        """
        p = 'uploaded.txt'
        f = self.path(p)
        with open(f, 'w') as fd:
            fd.write("contents")
        with hide('everything'):
            retval = put(f, p)
        eq_(retval, [p])

    @server()
    def test_put_returns_list_of_remote_paths_with_stringio(self):
        """
        put() should return a one-item iterable when uploading from a StringIO
        """
        f = 'uploaded.txt'
        with hide('everything'):
            eq_(put(StringIO('contents'), f), [f])

    @server()
    def test_put_return_value_failed_attribute(self):
        """
        put()'s return value should indicate any paths which failed to upload.
        """
        with settings(hide('everything'), warn_only=True):
            f = StringIO('contents')
            retval = put(f, '/nonexistent/directory/structure')
        eq_(["<StringIO>"], retval.failed)
        assert not retval.succeeded

    #
    # Interactions with cd()
    #
    @server()
    def test_cd_should_apply_to_put(self):
        """
        put() should honor env.cwd for relative remote paths
        """
        f = 'test.txt'
        d = '/empty_folder'
        local = self.path(f)
        with open(local, 'w') as fd:
            fd.write('test')
        with nested(cd(d), hide('everything')):
            put(local, f)
        assert self.exists_remotely('%s/%s' % (d, f))

    @server(files={'/tmp/test.txt': 'test'})
    def test_cd_should_apply_to_get(self):
        """
        get() should honor env.cwd for relative remote paths
        """
        local = self.path('test.txt')
        with nested(cd('/tmp'), hide('everything')):
            get('test.txt', local)
        assert os.path.exists(local)

    @server()
    def test_cd_should_not_apply_to_absolute_put(self):
        """
        put() should not prepend env.cwd to absolute remote paths
        """
        local = self.path('test.txt')
        with open(local, 'w') as fd:
            fd.write('test')
        with nested(cd('/tmp'), hide('everything')):
            put(local, '/test.txt')
        assert not self.exists_remotely('/tmp/test.txt')
        assert self.exists_remotely('/test.txt')

    @server(files={'/test.txt': 'test'})
    def test_cd_should_not_apply_to_absolute_get(self):
        """
        get() should not prepend env.cwd to absolute remote paths
        """
        local = self.path('test.txt')
        with nested(cd('/tmp'), hide('everything')):
            get('/test.txt', local)
        assert os.path.exists(local)

    @server()
    def test_lcd_should_apply_to_put(self):
        """
        lcd() should apply to put()'s local_path argument
        """
        f = 'lcd_put_test.txt'
        d = 'subdir'
        local = self.path(d, f)
        os.makedirs(os.path.dirname(local))
        with open(local, 'w') as fd:
            fd.write("contents")
        with nested(lcd(self.path(d)), hide('everything')):
            put(f, '/')
        assert self.exists_remotely('/%s' % f)

    @server()
    def test_lcd_should_apply_to_get(self):
        """
        lcd() should apply to get()'s local_path argument
        """
        d = self.path('subdir')
        f = 'file.txt'
        with nested(lcd(d), hide('everything')):
            get(f, f)
        assert self.exists_locally(os.path.join(d, f))


#
# local()
#

# TODO: figure out how to mock subprocess, if it's even possible.
# For now, simply test to make sure local() does not raise exceptions with
# various settings enabled/disabled.

def test_local_output_and_capture():
    for capture in (True, False):
        for stdout in (True, False):
            for stderr in (True, False):
                hides, shows = ['running'], []
                if stdout:
                    hides.append('stdout')
                else:
                    shows.append('stdout')
                if stderr:
                    hides.append('stderr')
                else:
                    shows.append('stderr')
                with nested(hide(*hides), show(*shows)):
                    d = "local(): capture: %r, stdout: %r, stderr: %r" % (
                        capture, stdout, stderr
                    )
                    local.description = d
                    yield local, "echo 'foo' >/dev/null", capture
                    del local.description
