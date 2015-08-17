import os
import shutil
import tempfile
from StringIO import StringIO

from spec import Spec, ok_, eq_

from fabric import Transfer, Connection


class Transfer_(Spec):
    def setup(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.tmpdir)

    class get:
        def setup(self):
            self.t = Transfer(Connection('localhost'))
            self.remote = os.path.join(
                os.path.dirname(__file__), '_support', 'file.txt'
            )

        def base_case(self):
            # Copy file from support to tempdir
            local = os.path.join(self.tmpdir, 'file.txt')
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
