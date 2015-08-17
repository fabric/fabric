import os
import shutil
import stat
import tempfile
from StringIO import StringIO

from spec import Spec, ok_, eq_

from fabric import Transfer, Connection


class Transfer_(Spec):
    def setup(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.tmpdir)

    def _tmp(self, *parts):
        return os.path.join(self.tmpdir, *parts)

    def _support(self, *parts):
        return os.path.join(os.path.dirname(__file__), '_support', *parts)

    class get:
        def setup(self):
            self.t = Transfer(Connection('localhost'))
            self.remote = self._support('file.txt')

        def base_case(self):
            # Copy file from support to tempdir
            local = self._tmp('file.txt')
            result = self.t.get(remote=self.remote, local=local)
            # Make sure it arrived
            ok_(os.path.exists(local))
            eq_(open(local).read(), 'yup\n')
            # Sanity check result object
            eq_(result.remote, self.remote)
            eq_(result.local, local)

        def file_like_objects(self):
            fd = StringIO()
            result = self.t.get(remote=self.remote, local=fd)
            eq_(fd.getvalue(), 'yup\n')
            eq_(result.remote, self.remote)
            ok_(result.local is fd)

        def mode_preservation(self):
            # This file has an unusual, highly unlikely to be default umask,
            # set of permissions (oct 641, aka -rw-r----x)
            local = self._tmp('funky-perms.txt')
            remote = self._support('funky-perms.txt')
            self.t.get(remote=remote, local=local)
            eq_(stat.S_IMODE(os.stat(local).st_mode), 0641)
