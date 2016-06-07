import os
import shutil
import stat
import tempfile
from StringIO import StringIO

from spec import Spec, ok_, eq_

from fabric import Connection


class Transfer_(Spec):
    def setup(self):
        # Apply realpath() because sometimes symlinks pop up and make life
        # messy (e.g. /var/tmp is really /private/var/tmp on OS X)
        self.tmpdir = os.path.realpath(tempfile.mkdtemp())

    def teardown(self):
        shutil.rmtree(self.tmpdir)

    def _tmp(self, *parts):
        return os.path.join(self.tmpdir, *parts)

    def _support(self, *parts):
        return os.path.join(os.path.dirname(__file__), '_support', *parts)


    class get:
        def setup(self):
            self.c = Connection('localhost')
            self.remote = self._support('file.txt')

        def base_case(self):
            # Copy file from support to tempdir
            # TODO: consider path.py for contextmanager
            cwd = os.getcwd()
            os.chdir(self.tmpdir)
            try:
                result = self.c.get(self.remote)
            finally:
                os.chdir(cwd)

            # Make sure it arrived
            local = self._tmp('file.txt')
            ok_(os.path.exists(local))
            eq_(open(local).read(), 'yup\n')
            # Sanity check result object
            eq_(result.remote, self.remote)
            eq_(result.orig_remote, self.remote)
            eq_(result.local, local)
            eq_(result.orig_local, None)

        def file_like_objects(self):
            fd = StringIO()
            result = self.c.get(remote=self.remote, local=fd)
            eq_(fd.getvalue(), 'yup\n')
            eq_(result.remote, self.remote)
            ok_(result.local is fd)

        def mode_preservation(self):
            # This file has an unusual, highly unlikely to be default umask,
            # set of permissions (oct 641, aka -rw-r----x)
            local = self._tmp('funky-perms.txt')
            remote = self._support('funky-perms.txt')
            self.c.get(remote=remote, local=local)
            eq_(stat.S_IMODE(os.stat(local).st_mode), 0o641)


    class put:
        def setup(self):
            self.c = Connection('localhost')
            self.remote = self._tmp('file.txt')

        def base_case(self):
            # Copy file from 'local' (support dir) to 'remote' (tempdir)
            # TODO: consider path.py for contextmanager
            cwd = os.getcwd()
            os.chdir(self._support())
            try:
                # TODO: wrap chdir at the Connection level
                self.c.sftp().chdir(self._tmp())
                result = self.c.put('file.txt')
            finally:
                os.chdir(cwd)

            # Make sure it arrived
            ok_(os.path.exists(self.remote))
            eq_(open(self.remote).read(), 'yup\n')
            # Sanity check result object
            eq_(result.remote, self.remote)
            eq_(result.orig_remote, None)
            eq_(result.local, self._support('file.txt'))
            eq_(result.orig_local, 'file.txt')

        def file_like_objects(self):
            fd = StringIO()
            fd.write("yup\n")
            result = self.c.put(local=fd, remote=self.remote)
            eq_(open(self.remote).read(), "yup\n")
            eq_(result.remote, self.remote)
            ok_(result.local is fd)

        def mode_preservation(self):
            # This file has an unusual, highly unlikely to be default umask,
            # set of permissions (oct 641, aka -rw-r----x)
            local = self._support('funky-perms.txt')
            remote = self._tmp('funky-perms.txt')
            self.c.put(remote=remote, local=local)
            eq_(stat.S_IMODE(os.stat(remote).st_mode), 0o641)
