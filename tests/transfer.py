from StringIO import StringIO

from mock import Mock, call
from spec import Spec, ok_, eq_, raises
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
            @mock_sftp()
            def local_None_uses_remote_filename(self, sftp, transfer):
                eq_(transfer.get('file').local, '/local/file')

            @mock_sftp()
            def local_empty_string_uses_remote_filename(self, sftp, transfer):
                eq_(transfer.get('file', local='').local, '/local/file')

            @mock_sftp()
            @raises(TypeError)
            def remote_arg_is_required(self, sftp, transfer):
                transfer.get()

            @mock_sftp()
            @raises(ValueError)
            def remote_arg_cannot_be_None(self, sftp, transfer):
                transfer.get(None)

            @mock_sftp()
            @raises(ValueError)
            def remote_arg_cannot_be_empty_string(self, sftp, transfer):
                transfer.get('')

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


    class put:
        class basics:
            @mock_sftp(expose_os=True)
            def accepts_single_local_path_posarg(
                self, sftp, transfer, mock_os
            ):
                transfer.put('file')
                sftp.put.assert_called_with(
                    localpath='/local/file',
                    remotepath='/remote/file',
                )

            @mock_sftp()
            def accepts_local_and_remote_kwargs(self, sftp, transfer):
                transfer.put(
                    remote='path1',
                    local='path2',
                )
                sftp.put.assert_called_with(
                    remotepath='/remote/path1',
                    localpath='/local/path2',
                )

            @mock_sftp(expose_os=True)
            def returns_rich_Result_object(self, sftp, transfer, mock_os):
                cxn = Connection('host')
                result = Transfer(cxn).put('file')
                eq_(result.orig_remote, None)
                eq_(result.remote, '/remote/file')
                eq_(result.orig_local, 'file')
                eq_(result.local, '/local/file')
                ok_(result.connection is cxn)
                # TODO: timing info
                # TODO: bytes-transferred info

        class path_arg_edge_cases:
            @mock_sftp()
            def remote_None_uses_local_filename(self, sftp, transfer):
                eq_(transfer.put('file').remote, '/remote/file')

            @mock_sftp()
            def remote_empty_string_uses_local_filename(self, sftp, transfer):
                eq_(transfer.put('file', remote='').remote, '/remote/file')

            @mock_sftp()
            @raises(ValueError)
            def remote_cant_be_empty_if_local_file_like(self, sftp, transfer):
                transfer.put(StringIO())

            @mock_sftp()
            @raises(TypeError)
            def local_arg_is_required(self, sftp, transfer):
                transfer.put()

            @mock_sftp()
            @raises(ValueError)
            def local_arg_cannot_be_None(self, sftp, transfer):
                transfer.put(None)

            @mock_sftp()
            @raises(ValueError)
            def local_arg_cannot_be_empty_string(self, sftp, transfer):
                transfer.put('')

        class file_like_local_paths:
            "file-like local paths"
            @mock_sftp()
            def _put_from_stringio(self, sftp, transfer):
                fd = StringIO()
                result = transfer.put(fd, remote='file')
                # Note: putfo, not put
                sftp.putfo.assert_called_with(
                    remotepath='/remote/file',
                    fl=fd,
                )
                return result, fd

            def remote_path_from_local_StringIO(self):
                self._put_from_stringio()

            @mock_sftp()
            def local_FLOs_are_rewound_before_putting(self, sftp, transfer):
                fd = Mock()
                fd.tell.return_value = 17
                transfer.put(fd, remote='file')
                seek_calls = fd.seek.call_args_list
                eq_(seek_calls, [call(0), call(17)])

            def result_contains_fd_for_local_path(self):
                result, fd = self._put_from_stringio()
                eq_(result.remote, '/remote/file')
                ok_(result.local is fd)

        class mode_concerns:
            @mock_sftp(expose_os=True)
            def preserves_local_mode_by_default(
                self, sftp, transfer, mock_os
            ):
                mock_os.stat.return_value.st_mode = 33188 # realistic for 0644
                transfer.put('file')
                sftp.chmod.assert_called_with('/remote/file', 0644)

            @mock_sftp(expose_os=True)
            def allows_disabling_local_mode_preservation(
                self, sftp, transfer, mock_os
            ):
                transfer.put('file', preserve_mode=False)
                ok_(not sftp.chmod.called)
