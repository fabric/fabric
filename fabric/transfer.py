"""
File transfer via SFTP and/or SCP.
"""

import os
import stat

# TODO: figure out best way to direct folks seeking rsync, to patchwork's rsync
# call (which needs updating to use invoke.run() & fab 2 connection methods,
# but is otherwise suitable).
# UNLESS we want to try and shoehorn it into this module after all? Delegate
# any recursive get/put to it? Requires users to have rsync available of
# course.


class Transfer(object):
    """
    `.Connection` wrapping class responsible for managing file upload/download.
    """
    # TODO: SFTP clear default, but how to do SCP? subclass? init kwarg?

    def __init__(self, connection):
        self.connection = connection

    def get(self, remote, local=None, preserve_mode=True):
        """
        Download a file from the current connection to the local filesystem.

        :param str remote:
            Remote file to download.

            Must evaluate to a file (not a directory). May be relative (from
            remote default CWD, typically connecting user's ``$HOME``) or
            absolute.

        :param local:
            Local path to store downloaded file in, or a file-like object.

            **If None is given** (the default), the remote file is downloaded
            to the current working directory (as seen by `os.cwd`) using its
            remote filename.

            **If a string is given**, it should be a path to a local directory
            or file and is subject to similar behavior as that seen by common
            Unix utilities or OpenSSH's ``sftp`` or ``scp`` tools.

            For example, if the local path is a directory, the remote path's
            base filename will be added onto it (so ``get('foo/bar/file.txt',
            '/tmp/')`` would result in creation or overwriting of
            ``/tmp/file.txt``).

            .. note::
                When dealing with nonexistent file paths, normal Python file
                handling concerns come into play - for example, a ``local``
                path containing non-leaf directories which do not exist, will
                typically result in an `OSError`.

            **If a file-like object is given**, the contents of the remote file
            are simply written into it.

            .. note::
                The file-like object will be 'rewound' to the beginning using
                `file.seek` to ensure a clean write.

        :param bool preserve_mode:
            Whether to `os.chmod` the local file so it matches the remote
            file's mode (default: ``True``).

        :returns: A `.Result` object.
        """
        # TODO: how does this API change if we want to implement
        # remote-to-remote file transfer?
        # TODO: handle v1's string interpolation bits, especially the default
        # one, or at least think about how that would work re: split between
        # single and multiple server targets.
        # TODO: callback support
        # TODO: how best to allow changing the behavior/semantics of
        # remote/local (e.g. users might want 'safer' behavior that complains
        # instead of overwriting existing files) - this likely ties into the
        # "how to handle recursive/rsync" and "how to handle scp" questions

        # Massage local path
        if local is None:
            local = os.getcwd()
        # Run Paramiko-level .get() (side-effects only. womp.)
        sftp = self.connection.sftp()
        # TODO: how can we get the actual path paramiko is operating on (so
        # we can present the full paths used)? do we suck it up and just do all
        # the munging we want to do here? or do we push a lot of this deeper
        # into paramiko now instead of later? or do we just ignore?
        #
        # TODO: probably preserve warning message from v1 when overwriting
        # existing files. Use logging for that obviously.
        #
        # If local appears to be a file-like object, use sftp.getfo, not get
        if hasattr(local, 'write') and callable(local.write):
            sftp.getfo(remotepath=remote, fl=local)
        else:
            sftp.get(remotepath=remote, localpath=local)
            # Set mode to same as remote end
            # TODO: Push this down into SFTPClient sometime (requires backwards
            # incompat release.)
            #
            mode = stat.S_IMODE(sftp.stat(remote).st_mode)
            if preserve_mode:
                os.chmod(local, mode)
        # Return something useful
        return Result(remote=remote, local=local, connection=self.connection)

    def put(self, local, remote=None, preserve_mode=True):
        """
        Upload a file from the local filesystem to the current connection.

        :param local:
            Local path of file to upload, or a file-like object.

            **If a string is given**, it should be a path to a local (regular)
            file (not a directory).

            .. note::
                When dealing with nonexistent file paths, normal Python file
                handling concerns come into play - for example, trying to
                upload a nonexistent ``local`` path will typically result in an
                `OSError`.

            **If a file-like object is given**, its contents are written to the
            remote file path.

            .. note::
                The file-like object will be 'rewound' to the beginning using
                `file.seek` to ensure a clean read.

        :param str remote:
            Remote path to which the local file will be written; is subject to
            similar behavior as that seen by common Unix utilities or OpenSSH's
            ``sftp`` or ``scp`` tools.

            If ``None`` is given (the default), the remote current working
            directory (typically the connecting user's home directory) is
            assumed.

            .. note::
                When ``local`` is a file-like object, ``remote`` is required
                and must refer to a valid file path (not a directory).

        :param bool preserve_mode:
            Whether to ``chmod`` the remote file so it matches the local file's
            mode (default: ``True``).

        :returns: A `.Result` object.
        """
        # TODO: preserve honoring of  "name" attribute of file-like objects as
        # in v1? did we just make that shit up or is it an actual part of the
        # api in newer Pythons?


class Result(object):
    """
    A container for information about the result of a file transfer.

    See individual attribute/method documentation below for details.

    .. note::
        Unlike similar classes such as `invoke.runners.Result` or
        `fabric.runners.RemoteResult`, this class has no useful truthiness
        behavior. If a file transfer fails, some exception will be raised,
        either an `OSError` or an error from within Paramiko (such as when the
        local copy of the file is not the same size as the remote).
    """
    # TODO: how does this differ from put vs get?
    def __init__(self, local, remote, connection):
        #: The local path the file was saved as, or the object it was saved
        #: into if a file-like object was given instead.
        self.local = local
        #: The remote path downloaded from.
        self.remote = remote
        #: The `.Connection` object this result was obtained from.
        self.connection = connection

    # TODO: ensure str/repr makes it easily differentiable from run() or
    # local() result objects (and vice versa).
