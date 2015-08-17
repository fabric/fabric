import os
from StringIO import StringIO

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

        class file_local_path:
            @_mocked_client
            def _get_to_stringio(self, Client):
                sftp = _sftp(Client)
                fd = StringIO()
                r = Transfer(Connection('host')).get('remote-path', local=fd)
                # Note: getfo, not get
                sftp.getfo.assert_called_with(
                    remotepath='remote-path',
                    fl=fd,
                )
                return r, fd

            def remote_path_to_local_StringIO(self):
                self._get_to_stringio()

            def result_contains_None_for_local_path(self):
                result, fd = self._get_to_stringio()
                eq_(result.remote, 'remote-path')
                ok_(result.local is fd)

        class mode_concerns:
            def preserves_remote_mode_by_default(self):
                # remote foo.txt is something unlikely to be default local
                # umask (but still readable by ourselves) -> get() -> local
                # file matches remote mode.
                skip()
