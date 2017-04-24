from __future__ import with_statement

import os
import re
import shutil
import sys

from contextlib import nested
from StringIO import StringIO

from nose.tools import ok_, raises
from fudge import patched_context, with_fakes, Fake
from fudge.inspector import arg as fudge_arg
from mock_streams import mock_streams
from paramiko.sftp_client import SFTPClient  # for patching

from fabric.state import env, output
from fabric.operations import require, prompt, _sudo_prefix, _shell_wrap, \
    _shell_escape
from fabric.api import get, put, hide, show, cd, lcd, local, run, sudo, quiet
from fabric.context_managers import settings
from fabric.exceptions import CommandTimeout

from fabric.sftp import SFTP
from fabric.decorators import with_settings
from utils import (eq_, aborts, assert_contains, eq_contents,
                   with_patched_input, FabricTest)
from server import server, FILES

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


@aborts
def test_require_single_missing_key():
    """
    When given a single non-existent key, require() aborts
    """
    require('blah')


@aborts
def test_require_multiple_missing_keys():
    """
    When given multiple non-existent keys, require() aborts
    """
    require('foo', 'bar')


@aborts
def test_require_mixed_state_keys():
    """
    When given mixed-state keys, require() aborts
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


@aborts
def test_require_iterable_provided_by_key():
    """
    When given a provided_by iterable value, require() aborts
    """
    # 'version' is one of the default values, so we know it'll be there
    def fake_providing_function():
        pass
    require('foo', provided_by=[fake_providing_function])


@aborts
def test_require_noniterable_provided_by_key():
    """
    When given a provided_by noniterable value, require() aborts
    """
    # 'version' is one of the default values, so we know it'll be there
    def fake_providing_function():
        pass
    require('foo', provided_by=fake_providing_function)


@aborts
def test_require_key_exists_empty_list():
    """
    When given a single existing key but the value is an empty list, require()
    aborts
    """
    # 'hosts' is one of the default values, so we know it'll be there
    require('hosts')


@aborts
@with_settings(foo={})
def test_require_key_exists_empty_dict():
    """
    When given a single existing key but the value is an empty dict, require()
    aborts
    """
    require('foo')


@aborts
@with_settings(foo=())
def test_require_key_exists_empty_tuple():
    """
    When given a single existing key but the value is an empty tuple, require()
    aborts
    """
    require('foo')


@aborts
@with_settings(foo=set())
def test_require_key_exists_empty_set():
    """
    When given a single existing key but the value is an empty set, require()
    aborts
    """
    require('foo')


@with_settings(foo=0, bar=False)
def test_require_key_exists_false_primitive_values():
    """
    When given keys that exist with primitive values that evaluate to False,
    require() throws no exception
    """
    require('foo', 'bar')


@with_settings(foo=['foo'], bar={'bar': 'bar'}, baz=('baz',), qux=set('qux'))
def test_require_complex_non_empty_values():
    """
    When given keys that exist with non-primitive values that are not empty,
    require() throws no exception
    """
    require('foo', 'bar', 'baz', 'qux')


#
# prompt()
#

def p(x):
    sys.stdout.write(x)


@mock_streams('stdout')
@with_patched_input(p)
def test_prompt_appends_space():
    """
    prompt() appends a single space when no default is given
    """
    s = "This is my prompt"
    prompt(s)
    eq_(sys.stdout.getvalue(), s + ' ')


@mock_streams('stdout')
@with_patched_input(p)
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
        _sudo_prefix(user="foo", group=None),
        "%s -u \"foo\" " % (env.sudo_prefix % env)
    )


def test_sudo_prefix_without_user():
    """
    _sudo_prefix() returns standard prefix when user is empty
    """
    eq_(_sudo_prefix(user=None, group=None), env.sudo_prefix % env)


def test_sudo_prefix_with_group():
    """
    _sudo_prefix() returns prefix plus -g flag for nonempty group
    """
    eq_(
        _sudo_prefix(user=None, group="foo"),
        "%s -g \"foo\" " % (env.sudo_prefix % env)
    )


def test_sudo_prefix_with_user_and_group():
    """
    _sudo_prefix() returns prefix plus -u and -g for nonempty user and group
    """
    eq_(
        _sudo_prefix(user="foo", group="bar"),
        "%s -u \"foo\" -g \"bar\" " % (env.sudo_prefix % env)
    )


@with_settings(use_shell=True)
def test_shell_wrap():
    prefix = "prefix"
    command = "command"
    for description, shell, sudo_prefix, result in (
        ("shell=True, sudo_prefix=None",
            True, None, '%s "%s"' % (env.shell, command)),
        ("shell=True, sudo_prefix=string",
            True, prefix, prefix + ' %s "%s"' % (env.shell, command)),
        ("shell=False, sudo_prefix=None",
            False, None, command),
        ("shell=False, sudo_prefix=string",
            False, prefix, prefix + " " + command),
    ):
        eq_.description = "_shell_wrap: %s" % description
        yield eq_, _shell_wrap(command, shell_escape=True, shell=shell, sudo_prefix=sudo_prefix), result
        del eq_.description


@with_settings(use_shell=True)
def test_shell_wrap_escapes_command_if_shell_is_true():
    """
    _shell_wrap() escapes given command if shell=True
    """
    cmd = "cd \"Application Support\""
    eq_(
        _shell_wrap(cmd, shell_escape=True, shell=True),
        '%s "%s"' % (env.shell, _shell_escape(cmd))
    )


@with_settings(use_shell=True)
def test_shell_wrap_does_not_escape_command_if_shell_is_true_and_shell_escape_is_false():
    """
    _shell_wrap() does no escaping if shell=True and shell_escape=False
    """
    cmd = "cd \"Application Support\""
    eq_(
        _shell_wrap(cmd, shell_escape=False, shell=True),
        '%s "%s"' % (env.shell, cmd)
    )


def test_shell_wrap_does_not_escape_command_if_shell_is_false():
    """
    _shell_wrap() does no escaping if shell=False
    """
    cmd = "cd \"Application Support\""
    eq_(_shell_wrap(cmd, shell_escape=True, shell=False), cmd)


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


class TestQuietAndWarnKwargs(FabricTest):
    @server(responses={'wat': ["", "", 1]})
    def test_quiet_implies_warn_only(self):
        # Would raise an exception if warn_only was False
        eq_(run("wat", quiet=True).failed, True)

    @server()
    @mock_streams('both')
    def test_quiet_implies_hide_everything(self):
        run("ls /", quiet=True)
        eq_(sys.stdout.getvalue(), "")
        eq_(sys.stderr.getvalue(), "")

    @server(responses={'hrm': ["", "", 1]})
    @mock_streams('both')
    def test_warn_only_is_same_as_settings_warn_only(self):
        eq_(run("hrm", warn_only=True).failed, True)

    @server()
    @mock_streams('both')
    def test_warn_only_does_not_imply_hide_everything(self):
        run("ls /simple", warn_only=True)
        assert sys.stdout.getvalue() != ""


class TestMultipleOKReturnCodes(FabricTest):
    @server(responses={'no srsly its ok': ['', '', 1]})
    def test_expand_to_include_1(self):
        with settings(quiet(), ok_ret_codes=[0, 1]):
            eq_(run("no srsly its ok").succeeded, True)


slow_server = server(responses={'slow': ['', '', 0, 3]})
slow = lambda x: slow_server(raises(CommandTimeout)(x))

class TestRun(FabricTest):
    """
    @server-using generic run()/sudo() tests
    """
    @slow
    def test_command_timeout_via_env_var(self):
        env.command_timeout = 2 # timeout after 2 seconds
        with hide('everything'):
            run("slow")

    @slow
    def test_command_timeout_via_kwarg(self):
        with hide('everything'):
            run("slow", timeout=2)

    @slow
    def test_command_timeout_via_env_var_in_sudo(self):
        env.command_timeout = 2 # timeout after 2 seconds
        with hide('everything'):
            sudo("slow")

    @slow
    def test_command_timeout_via_kwarg_of_sudo(self):
        with hide('everything'):
            sudo("slow", timeout=2)


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

    @server(files={'/top/%a/%(/%()/%(x)/%(no)s/%(host)s/%d': 'yo'})
    def test_get_with_format_chars_on_server(self):
        """
        get('*') with format symbols (%) on remote paths should not break
        """
        remote = '*'
        with hide('everything'):
            get(remote, self.path())

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

    @server(files={'/base/dir with spaces/file': 'stuff!'})
    def test_get_file_from_relative_path_with_spaces(self):
        """
        get('file') should work when the remote path contains spaces
        """
        # from nose.tools import set_trace; set_trace()
        with hide('everything'):
            with cd('/base/dir with spaces'):
                eq_(get('file', self.path()), [self.path('file')])

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
    def test_nonexistent_glob_should_not_create_empty_files(self):
        path = self.path()
        with settings(hide('everything'), warn_only=True):
            get('/nope*.txt', path)
        assert not self.exists_locally(os.path.join(path, 'nope*.txt'))

    @server()
    def test_nonexistent_glob_raises_error(self):
        try:
            with hide('everything', 'aborts'):
                get('/nope*.txt', self.path())
        except SystemExit as e:
            assert 'No such file' in e.message
        else:
            assert False

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

    @server()
    @with_fakes
    def test_get_use_sudo(self):
        """
        get(use_sudo=True) works by copying to a temporary path, downloading it and then removing it at the end
        """
        fake_run = Fake('_run_command', callable=True, expect_call=True).with_matching_args(
            fudge_arg.startswith('cp -p "/etc/apache2/apache2.conf" "'), True, True, None
        ).next_call().with_matching_args(
            fudge_arg.startswith('chown username "'), True, True, None,
        ).next_call().with_matching_args(
            fudge_arg.startswith('chmod 400 "'), True, True, None,
        ).next_call().with_matching_args(
            fudge_arg.startswith('rm -f "'), True, True, None,
        )
        fake_get = Fake('get', callable=True, expect_call=True)

        with hide('everything'):
            with patched_context('fabric.operations', '_run_command', fake_run):
                with patched_context(SFTPClient, 'get', fake_get):
                    retval = get('/etc/apache2/apache2.conf', self.path(), use_sudo=True)
                    # check that the downloaded file has the same name as the one requested
                    assert retval[0].endswith('apache2.conf')

    @server()
    @with_fakes
    def test_get_use_sudo_temp_dir(self):
        """
        get(use_sudo=True, temp_dir="/tmp") works by copying to /tmp/..., downloading it and then removing it at the end
        """
        fake_run = Fake('_run_command', callable=True, expect_call=True).with_matching_args(
            fudge_arg.startswith('cp -p "/etc/apache2/apache2.conf" "/tmp/'), True, True, None,
        ).next_call().with_matching_args(
            fudge_arg.startswith('chown username "/tmp/'), True, True, None,
        ).next_call().with_matching_args(
            fudge_arg.startswith('chmod 400 "/tmp/'), True, True, None,
        ).next_call().with_matching_args(
            fudge_arg.startswith('rm -f "/tmp/'), True, True, None,
        )
        fake_get = Fake('get', callable=True, expect_call=True).with_args(
            fudge_arg.startswith('/tmp/'), fudge_arg.any_value())

        with hide('everything'):
            with patched_context('fabric.operations', '_run_command', fake_run):
                with patched_context(SFTPClient, 'get', fake_get):
                    retval = get('/etc/apache2/apache2.conf', self.path(), use_sudo=True, temp_dir="/tmp")
                    # check that the downloaded file has the same name as the one requested
                    assert retval[0].endswith('apache2.conf')

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

    @server()
    def test_put_sends_all_files_with_glob(self):
        """
        put() should send all items that match a glob.
        """
        paths = ['foo1.txt', 'foo2.txt']
        glob = 'foo*.txt'
        remote_directory = '/'
        for path in paths:
            self.mkfile(path, 'foo!')

        with hide('everything'):
            retval = put(self.path(glob), remote_directory)
        eq_(sorted(retval), sorted([remote_directory + path for path in paths]))

    @server()
    def test_put_sends_correct_file_with_globbing_off(self):
        """
        put() should send a file with a glob pattern in the path, when globbing disabled.
        """
        text = "globbed!"
        local = self.mkfile('foo[bar].txt', text)
        local2 = self.path('foo2.txt')
        with hide('everything'):
            put(local, '/', use_glob=False)
            get('/foo[bar].txt', local2)
        eq_contents(local2, text)

    @server()
    @with_fakes
    def test_put_use_sudo(self):
        """
        put(use_sudo=True) works by uploading a the `local_path` to a temporary path and then moving it to a `remote_path`
        """
        fake_run = Fake('_run_command', callable=True, expect_call=True).with_matching_args(
            fudge_arg.startswith('mv "'), True, True, None,
        )
        fake_put = Fake('put', callable=True, expect_call=True)

        local_path = self.mkfile('foobar.txt', "baz")
        with hide('everything'):
            with patched_context('fabric.operations', '_run_command', fake_run):
                with patched_context(SFTPClient, 'put', fake_put):
                    retval = put(local_path, "/", use_sudo=True)
                    # check that the downloaded file has the same name as the one requested
                    assert retval[0].endswith('foobar.txt')

    @server()
    @with_fakes
    def test_put_use_sudo_temp_dir(self):
        """
        put(use_sudo=True, temp_dir='/tmp/') works by uploading a file to /tmp/ and then moving it to a `remote_path`
        """
        # the sha1 hash is the unique filename of the file being downloaded. sha1(<filename>)
        fake_run = Fake('_run_command', callable=True, expect_call=True).with_matching_args(
            fudge_arg.startswith('mv "'), True, True, None,
        )
        fake_put = Fake('put', callable=True, expect_call=True)

        local_path = self.mkfile('foobar.txt', "baz")
        with hide('everything'):
            with patched_context('fabric.operations', '_run_command', fake_run):
                with patched_context(SFTPClient, 'put', fake_put):
                    retval = put(local_path, "/", use_sudo=True, temp_dir='/tmp/')
                    # check that the downloaded file has the same name as the one requested
                    assert retval[0].endswith('foobar.txt')


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

    @server()
    @mock_streams('stdout')
    def test_stringio_without_name(self):
        file_obj = StringIO(u'test data')
        put(file_obj, '/')
        assert re.search('<file obj>', sys.stdout.getvalue())

    @server()
    @mock_streams('stdout')
    def test_stringio_with_name(self):
        """If a file object (StringIO) has a name attribute, use that in output"""
        file_obj = StringIO(u'test data')
        file_obj.name = 'Test StringIO Object'
        put(file_obj, '/')
        assert re.search(file_obj.name, sys.stdout.getvalue())


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


class TestRunSudoReturnValues(FabricTest):
    @server()
    def test_returns_command_given(self):
        """
        run("foo").command == foo
        """
        with hide('everything'):
            eq_(run("ls /").command, "ls /")

    @server()
    def test_returns_fully_wrapped_command(self):
        """
        run("foo").real_command involves env.shell + etc
        """
        # FabTest turns use_shell off, we must reactivate it.
        # Doing so will cause a failure: server's default command list assumes
        # it's off, we're not testing actual wrapping here so we don't really
        # care. Just warn_only it.
        with settings(hide('everything'), warn_only=True, use_shell=True):
            # Slightly flexible test, we're not testing the actual construction
            # here, just that this attribute exists.
            ok_(env.shell in run("ls /").real_command)
