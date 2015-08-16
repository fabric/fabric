import os

from spec import Spec, skip, ok_, eq_
from mock import patch

from fabric import Transfer, Connection


# TODO: pull in all edge/corner case tests from fabric v1


_mocked_client = patch('fabric.connection.SSHClient')

def _sftp(Client):
    return Client.return_value.open_sftp.return_value


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
        class basics:
            @_mocked_client
            def accepts_single_remote_path_posarg(self, Client):
                sftp = _sftp(Client)
                Transfer(Connection('host')).get('remote-path')
                sftp.get.assert_called_with(
                    localpath=os.getcwd(),
                    remotepath='remote-path',
                )

            @_mocked_client
            def accepts_local_and_remote_kwargs(self, Client):
                sftp = _sftp(Client)
                Transfer(Connection('host')).get(
                    remote='remote-path',
                    local='local-path',
                )
                sftp.get.assert_called_with(
                    localpath='local-path',
                    remotepath='remote-path',
                )

            @_mocked_client
            def returns_rich_Result_object(self, Client):
                sftp = _sftp(Client)
                cxn = Connection('host')
                result = Transfer(cxn).get('remote-path')
                eq_(result.remote, 'remote-path')
                eq_(result.local, os.getcwd())
                ok_(result.connection is cxn)
                # TODO: timing info
                # TODO: bytes-transferred info

        class no_local_path:
            @_mocked_client
            def remote_relative_path_to_local_cwd(self, Client):
                #sftp = SSH_sftp(Client)
                #self.t.get('foo.txt')
                #sftp.get.assert_called_with('foo.txt', 'foo.txt')
                skip()

            def remote_absolute_path_to_local_cwd(self):
                # t.get('/tmp/foo.txt') -> ./foo.txt
                skip()

        class string_local_path:
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

        class file_local_path:
            def remote_relative_path_to_local_StringIO(self):
                # s = StringIO(); t.get('foo.txt', s) -> s filled up
                skip()

            def remote_absolute_path_to_local_StringIO(self):
                # s = StringIO(); t.get('/tmp/foo.txt', s) -> s filled up
                skip()

            def result_contains_None_for_local_path(self):
                # s = StringIO(); r = t.get('foo.txt', s); r.local == None
                skip()

        class mode_concerns:
            def preserves_remote_mode_by_default(self):
                # remote foo.txt is something unlikely to be default local
                # umask (but still readable by ourselves) -> get() -> local
                # file matches remote mode.
                skip()
