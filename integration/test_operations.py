from __future__ import with_statement

from StringIO import StringIO
import os
import posixpath
import shutil

from fabric.api import run, path, put, sudo, abort, warn_only, env, cd
from fabric.contrib.files import exists

from utils import Integration


def assert_mode(path, mode):
    assert run("stat -c \"%%a\" \"%s\"" % path).stdout == mode


class TestOperations(Integration):
    filepath = "/tmp/whocares"
    dirpath = "/tmp/whatever/bin"
    not_owned = "/tmp/notmine"

    def setup(self):
        super(TestOperations, self).setup()
        run("mkdir -p %s" % " ".join([self.dirpath, self.not_owned]))

    def teardown(self):
        super(TestOperations, self).teardown()
        # Revert any chown crap from put sudo tests
        sudo("chown %s ." % env.user)
        # Nuke to prevent bleed
        sudo("rm -rf %s" % " ".join([self.dirpath, self.filepath]))
        sudo("rm -rf %s" % self.not_owned)

    def test_no_trailing_space_in_shell_path_in_run(self):
        put(StringIO("#!/bin/bash\necho hi"), "%s/myapp" % self.dirpath, mode="0755")
        with path(self.dirpath):
            assert run('myapp').stdout == 'hi'

    def test_string_put_mode_arg_doesnt_error(self):
        put(StringIO("#!/bin/bash\necho hi"), self.filepath, mode="0755")
        assert_mode(self.filepath, "755")

    def test_int_put_mode_works_ok_too(self):
        put(StringIO("#!/bin/bash\necho hi"), self.filepath, mode=0755)
        assert_mode(self.filepath, "755")

    def _chown(self, target):
        sudo("chown root %s" % target)

    def _put_via_sudo(self, source=None, target_suffix='myfile', **kwargs):
        # Ensure target dir prefix is not owned by our user (so we fail unless
        # the sudo part of things is working)
        self._chown(self.not_owned)
        source = source if source else StringIO("whatever")
        # Drop temp file into that dir, via use_sudo, + any kwargs
        return put(
            source,
            self.not_owned + '/' + target_suffix,
            use_sudo=True,
            **kwargs
        )

    def test_put_with_use_sudo(self):
        self._put_via_sudo()

    def test_put_with_dir_and_use_sudo(self):
        # Test cwd should be root of fabric source tree. Use our own folder as
        # the source, meh.
        self._put_via_sudo(source='integration', target_suffix='')

    def test_put_with_use_sudo_and_custom_temp_dir(self):
        # TODO: allow dependency injection in sftp.put or w/e, test it in
        # isolation instead.
        # For now, just half-ass it by ensuring $HOME isn't writable
        # temporarily.
        self._chown('.')
        self._put_via_sudo(temp_dir='/tmp')

    def test_put_with_use_sudo_dir_and_custom_temp_dir(self):
        self._chown('.')
        self._put_via_sudo(source='integration', target_suffix='', temp_dir='/tmp')

    def test_put_use_sudo_and_explicit_mode(self):
        # Setup
        target_dir = posixpath.join(self.filepath, 'blah')
        subdir = "inner"
        subdir_abs = posixpath.join(target_dir, subdir)
        filename = "whatever.txt"
        target_file = posixpath.join(subdir_abs, filename)
        run("mkdir -p %s" % subdir_abs)
        self._chown(subdir_abs)
        local_path = os.path.join('/tmp', filename)
        with open(local_path, 'w+') as fd:
            fd.write('stuff\n')
        # Upload + assert
        with cd(target_dir):
            put(local_path, subdir, use_sudo=True, mode='777')
        assert_mode(target_file, '777')

    def test_put_file_to_dir_with_use_sudo_and_mirror_mode(self):
        # Target for _put_via_sudo is a directory by default
        uploaded = self._put_via_sudo(
            source='integration/test_operations.py', mirror_local_mode=True
        )
        assert_mode(uploaded[0], '644')

    def test_put_directory_use_sudo_and_spaces(self):
        localdir = 'I have spaces'
        localfile = os.path.join(localdir, 'file.txt')
        os.mkdir(localdir)
        with open(localfile, 'w') as fd:
            fd.write('stuff\n')
        try:
            uploaded = self._put_via_sudo(localdir, target_suffix='')
            # Kinda dumb, put() would've died if it couldn't do it, but.
            assert exists(uploaded[0])
            assert exists(posixpath.dirname(uploaded[0]))
        finally:
            shutil.rmtree(localdir)
