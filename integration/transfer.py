import os
import stat
from io import BytesIO

from py import path

from fabric import Connection


def _support(*parts):
    return os.path.join(os.path.dirname(__file__), "_support", *parts)


class Transfer_:
    class get:
        def setup(self):
            self.c = Connection("localhost")
            self.remote = _support("file.txt")

        def base_case(self, tmpdir):
            # Copy file from support to tempdir
            with tmpdir.as_cwd():
                result = self.c.get(self.remote)

            # Make sure it arrived
            local = tmpdir.join("file.txt")
            assert local.check()
            assert local.read() == "yup\n"
            # Sanity check result object
            assert result.remote == self.remote
            assert result.orig_remote == self.remote
            assert result.local == str(local)
            assert result.orig_local is None

        def file_like_objects(self):
            fd = BytesIO()
            result = self.c.get(remote=self.remote, local=fd)
            assert fd.getvalue() == b"yup\n"
            assert result.remote == self.remote
            assert result.local is fd

        def mode_preservation(self, tmpdir):
            # Use a dummy file which is given an unusual, highly unlikely to be
            # default umask, set of permissions (oct 641, aka -rw-r----x)
            local = tmpdir.join("funky-local.txt")
            remote = tmpdir.join("funky-remote.txt")
            remote.write("whatever")
            remote.chmod(0o641)
            self.c.get(remote=str(remote), local=str(local))
            assert stat.S_IMODE(local.stat().mode) == 0o641

    class put:
        def setup(self):
            self.c = Connection("localhost")
            self.remote = path.local.mkdtemp().join("file.txt").realpath()

        def base_case(self):
            # Copy file from 'local' (support dir) to 'remote' (tempdir)
            local_dir = _support()
            with path.local(local_dir).as_cwd():
                tmpdir = self.remote.dirpath()
                # TODO: wrap chdir at the Connection level
                self.c.sftp().chdir(str(tmpdir))
                result = self.c.put("file.txt")
            # Make sure it arrived
            assert self.remote.check()
            assert self.remote.read() == "yup\n"
            # Sanity check result object
            assert result.remote == self.remote
            assert result.orig_remote is None
            assert result.local == _support("file.txt")
            assert result.orig_local == "file.txt"

        def file_like_objects(self):
            fd = BytesIO()
            fd.write(b"yup\n")
            remote_str = str(self.remote)
            result = self.c.put(local=fd, remote=remote_str)
            assert self.remote.read() == "yup\n"
            assert result.remote == remote_str
            assert result.local is fd

        def mode_preservation(self, tmpdir):
            # Use a dummy file which is given an unusual, highly unlikely to be
            # default umask, set of permissions (oct 641, aka -rw-r----x)
            local = tmpdir.join("funky-local.txt")
            local.write("whatever")
            local.chmod(0o641)
            remote = tmpdir.join("funky-remote.txt")
            self.c.put(remote=str(remote), local=str(local))
            assert stat.S_IMODE(remote.stat().mode) == 0o641
