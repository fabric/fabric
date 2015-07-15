from spec import Spec, skip, ok_
from mock import patch

from fabric import Transfer, Connection


# TODO: pull in all edge/corner case tests from fabric v1

class Transfer_(Spec):
    class init:
        "__init__"
        def requires_connection(self):
            # Transfer() -> explodes
            try:
                Transfer()
            except TypeError:
                pass
            else:
                assert False, "Did not raise ArgumentError"
            # Transfer(Connection()) -> happy, exposes an attribute
            cxn = Connection('host')
            ok_(Transfer(cxn).connection is cxn)

    class get:
        def setup(self):
            self.t = Transfer(Connection('host'))

        class basics:
            def accepts_single_remote_path_posarg(self):
                # t.get('remote-path')
                skip()

            def accepts_local_and_remote_kwargs(self):
                # t.get(remote='remote-path', local='local-path')
                skip()

            def returns_rich_Result_object(self):
                # result = t.get('remote-path')
                # result has stuff, see tutorial
                skip()

        class no_local_path:
            @patch('fabric.connection.SSHClient')
            def remote_relative_path_to_local_cwd(self, SSHClient):
                sftp = SSHClient.return_value.open_sftp.return_value
                self.t.get('foo.txt')
                sftp.get.assert_called_with('foo.txt', 'foo.txt')

            def remote_absolute_path_to_local_cwd(self):
                # t.get('/tmp/foo.txt') -> ./foo.txt
                skip()

        class has_local_path:
            def remote_relative_path_to_local_relative_path(self):
                # t.get('foo.txt', local='bar.txt') -> ./bar.txt
                skip()

            def remote_absolute_path_to_local_relative_path(self):
                # t.get('/tmp/foo.txt', local='bar.txt') -> ./bar.txt
                skip()

            def remote_relative_path_to_local_absolute_path(self):
                # t.get('foo.txt', local='/tmp/bar.txt') -> /tmp/bar.txt
                skip()

            def remote_absolute_path_to_local_absolute_path(self):
                # t.get('/tmp/foo.txt', local='/tmp/bar.txt') -> /tmp/bar.txt
                skip()

        class mode_concerns:
            def preserves_remote_mode_by_default(self):
                # remote foo.txt is something unlikely to be default local
                # umask (but still readable by ourselves) -> get() -> local
                # file matches remote mode.
                skip()
