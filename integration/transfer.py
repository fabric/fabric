import os
import shutil
import tempfile

from spec import skip, Spec, ok_, eq_

from fabric import Transfer, Connection


class Transfer_(Spec):
    def setup(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.tmpdir)

    class get:
        def base_case(self):
            # Copy file from support to tempdir
            t = Transfer(Connection('localhost'))
            remote = os.path.join(
                os.path.dirname(__file__), '_support', 'file.txt'
            )
            local = os.path.join(self.tmpdir, 'file.txt')
            result = t.get(remote=remote, local=local)
            # Make sure it arrived
            ok_(os.path.exists(local))
            eq_(open(local).read(), 'yup')
            # Sanity check result object
            # TODO: this
