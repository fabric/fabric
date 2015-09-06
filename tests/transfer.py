from StringIO import StringIO

from spec import Spec, ok_, eq_, skip
from paramiko import SFTPAttributes

from fabric import Connection
from fabric.transfer import Transfer

from _utils import mock_sftp


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
        class basics:
            @mock_sftp(expose_os=True)
            def accepts_single_remote_path_posarg(
                self, sftp, transfer, mock_os
            ):
                transfer.get('file')
                sftp.get.assert_called_with(
                    localpath='/local/file',
                    remotepath='/remote/file',
                )

            @mock_sftp()
            def accepts_local_and_remote_kwargs(self, sftp, transfer):
                transfer.get(
                    remote='path1',
                    local='path2',
                )
                sftp.get.assert_called_with(
                    remotepath='/remote/path1',
                    localpath='/local/path2',
                )

            @mock_sftp(expose_os=True)
            def returns_rich_Result_object(self, sftp, transfer, mock_os):
                cxn = Connection('host')
                result = Transfer(cxn).get('file')
                eq_(result.orig_remote, 'file')
                eq_(result.remote, '/remote/file')
                eq_(result.orig_local, None)
                eq_(result.local, '/local/file')
                ok_(result.connection is cxn)
                # TODO: timing info
                # TODO: bytes-transferred info

        class path_arg_edge_cases:
            def local_None_uses_remote_filename(self):
                skip()

            def local_empty_string_uses_remote_filename(self):
                skip()

            def remote_arg_is_required(self):
                skip()

            def remote_arg_cannot_be_None(self):
                skip()

            def remote_arg_cannot_be_empty_string(self):
                skip()

        class file_like_local_paths:
            "file-like local paths"
            @mock_sftp()
            def _get_to_stringio(self, sftp, transfer):
                fd = StringIO()
                result = transfer.get('file', local=fd)
                # Note: getfo, not get
                sftp.getfo.assert_called_with(
                    remotepath='/remote/file',
                    fl=fd,
                )
                return result, fd

            def remote_path_to_local_StringIO(self):
                self._get_to_stringio()

            def result_contains_fd_for_local_path(self):
                result, fd = self._get_to_stringio()
                eq_(result.remote, '/remote/file')
                ok_(result.local is fd)

            def file_like_objects_are_rewound(self):
                skip()

        class mode_concerns:
            def setup(self):
                self.attrs = SFTPAttributes()
                self.attrs.st_mode = 0100644

            @mock_sftp(expose_os=True)
            def preserves_remote_mode_by_default(
                self, sftp, transfer, mock_os
            ):
                # Attributes obj reflecting a realistic 'extended' octal mode
                sftp.stat.return_value = self.attrs
                transfer.get('file', local='meh')
                # Expect os.chmod to be called with the scrubbed/shifted
                # version of same.
                mock_os.chmod.assert_called_with('/local/meh', 0644)

            @mock_sftp(expose_os=True)
            def allows_disabling_remote_mode_preservation(
                self, sftp, transfer, mock_os
            ):
                sftp.stat.return_value = self.attrs
                transfer.get('file', local='meh', preserve_mode=False)
                ok_(not mock_os.chmod.called)
