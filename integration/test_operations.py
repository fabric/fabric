from __future__ import with_statement

from StringIO import StringIO
import os
import posixpath
import shutil

from fabric.api import (
    run, path, put, sudo, abort, warn_only, env, cd, local, settings, get
)
from fabric.contrib.files import exists

from utils import Integration


def assert_mode(path, mode):
    remote_mode = run("stat -c \"%%a\" \"%s\"" % path).stdout
    assert remote_mode == mode, "remote %r != expected %r" % (remote_mode, mode)


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
        # Ensure mode of local file, umask varies on eg travis vs various
        # localhosts
        source = 'whatever.txt'
        try:
            local("touch %s" % source)
            local("chmod 644 %s" % source)
            # Target for _put_via_sudo is a directory by default
            uploaded = self._put_via_sudo(
                source=source, mirror_local_mode=True
            )
            assert_mode(uploaded[0], '644')
        finally:
            local("rm -f %s" % source)

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

    def test_agent_forwarding_functions(self):
        # When paramiko #399 is present this will hang indefinitely
        with settings(forward_agent=True):
            run('ssh-add -L')

    def test_get_with_use_sudo_unowned_file(self):
        # Ensure target is not normally readable by us
        target = self.filepath
        sudo("echo 'nope' > %s" % target)
        sudo("chown root:root %s" % target)
        sudo("chmod 0440 %s" % target)
        # Pull down with use_sudo, confirm contents
        local_ = StringIO()
        result = get(
            local_path=local_,
            remote_path=target,
            use_sudo=True,
        )
        assert local_.getvalue() == "nope\n"

    def test_get_with_use_sudo_groupowned_file(self):
        # Issue #1226: file gotten w/ use_sudo, file normally readable via
        # group perms (yes - so use_sudo not required - full use case involves
        # full-directory get() where use_sudo *is* required). Prior to fix,
        # temp file is chmod 404 which seems to cause perm denied due to group
        # membership (despite 'other' readability).
        target = self.filepath
        sudo("echo 'nope' > %s" % target)
        # Same group as connected user
        gid = run("id -g")
        sudo("chown root:%s %s" % (gid, target))
        # Same perms as bug use case (only really need group read)
        sudo("chmod 0640 %s" % target)
        # Do eet
        local_ = StringIO()
        result = get(
            local_path=local_,
            remote_path=target,
            use_sudo=True,
        )
        assert local_.getvalue() == "nope\n"

    def test_get_from_unreadable_dir(self):
        # Put file in dir as normal user
        remotepath = "%s/myfile.txt" % self.dirpath
        run("echo 'foo' > %s" % remotepath)
        # Make dir unreadable (but still executable - impossible to obtain
        # file if dir is both unreadable and unexecutable)
        sudo("chown root:root %s" % self.dirpath)
        sudo("chmod 711 %s" % self.dirpath)
        # Try gettin' it
        local_ = StringIO()
        get(local_path=local_, remote_path=remotepath)
        assert local_.getvalue() == 'foo\n'
