"""
File transfer via SFTP and/or SCP.
"""

import os
import posixpath
import stat

from invoke.util import debug  # TODO: actual logging! LOL

# TODO: figure out best way to direct folks seeking rsync, to patchwork's rsync
# call (which needs updating to use invoke.run() & fab 2 connection methods,
# but is otherwise suitable).
# UNLESS we want to try and shoehorn it into this module after all? Delegate
# any recursive get/put to it? Requires users to have rsync available of
# course.


class Transfer(object):
    """
    `.Connection`-wrapping class responsible for managing file upload/download.

    .. versionadded:: 2.0
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
            remote CWD, typically connecting user's ``$HOME``) or absolute.

        :param local:
            Local path to store downloaded file in, or a file-like object.

            **If None or another 'falsey'/empty value is given** (the default),
            the remote file is downloaded to the current working directory (as
            seen by `os.getcwd`) using its remote filename.

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

        :param bool preserve_mode:
            Whether to `os.chmod` the local file so it matches the remote
            file's mode (default: ``True``).

        :returns: A `.Result` object.

        .. versionadded:: 2.0
        """
        # TODO: how does this API change if we want to implement
        # remote-to-remote file transfer? (Is that even realistic?)
        # TODO: handle v1's string interpolation bits, especially the default
        # one, or at least think about how that would work re: split between
        # single and multiple server targets.
        # TODO: callback support
        # TODO: how best to allow changing the behavior/semantics of
        # remote/local (e.g. users might want 'safer' behavior that complains
        # instead of overwriting existing files) - this likely ties into the
        # "how to handle recursive/rsync" and "how to handle scp" questions

        sftp = self.connection.sftp()

        # Massage remote path
        if not remote:
            raise ValueError("Remote path must not be empty!")
        orig_remote = remote
        remote = posixpath.join(sftp.getcwd() or sftp.normalize("."), remote)

        # Massage local path:
        # - handle file-ness
        # - if path, fill with remote name if empty, & make absolute
        orig_local = local
        is_file_like = hasattr(local, "write") and callable(local.write)
        if not local:
            local = posixpath.basename(remote)
        if not is_file_like:
            local = os.path.abspath(local)

        # Run Paramiko-level .get() (side-effects only. womp.)
        # TODO: push some of the path handling into Paramiko; it should be
        # responsible for dealing with path cleaning etc.
        # TODO: probably preserve warning message from v1 when overwriting
        # existing files. Use logging for that obviously.
        #
        # If local appears to be a file-like object, use sftp.getfo, not get
        if is_file_like:
            sftp.getfo(remotepath=remote, fl=local)
        else:
            sftp.get(remotepath=remote, localpath=local)
            # Set mode to same as remote end
            # TODO: Push this down into SFTPClient sometime (requires backwards
            # incompat release.)
            if preserve_mode:
                remote_mode = sftp.stat(remote).st_mode
                mode = stat.S_IMODE(remote_mode)
                os.chmod(local, mode)
        # Return something useful
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )

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

        :param str remote:
            Remote path to which the local file will be written; is subject to
            similar behavior as that seen by common Unix utilities or OpenSSH's
            ``sftp`` or ``scp`` tools.

            If ``None`` or another 'falsey'/empty value is given (the default),
            the remote current working directory (typically the connecting
            user's home directory) is assumed.

            .. note::
                When ``local`` is a file-like object, ``remote`` is required
                and must refer to a valid file path (not a directory).

        :param bool preserve_mode:
            Whether to ``chmod`` the remote file so it matches the local file's
            mode (default: ``True``).

        :returns: A `.Result` object.

        .. versionadded:: 2.0
        """
        # TODO: preserve honoring of  "name" attribute of file-like objects as
        # in v1, so one CAN just upload to a directory? did we just make that
        # shit up or is it an actual part of the api in newer Pythons?
        sftp = self.connection.sftp()

        if not local:
            raise ValueError("Local path must not be empty!")

        is_file_like = hasattr(local, "write") and callable(local.write)

        # Massage remote path
        orig_remote = remote
        if not remote:
            if is_file_like:
                raise ValueError(
                    "Must give non-empty remote path when local is a file-like object!"  # noqa
                )
            else:
                remote = os.path.basename(local)
                debug("Massaged empty remote path into {!r}".format(remote))
        prejoined_remote = remote
        remote = posixpath.join(sftp.getcwd() or sftp.normalize("."), remote)
        if remote != prejoined_remote:
            msg = "Massaged relative remote path {!r} into {!r}"
            debug(msg.format(prejoined_remote, remote))

        # Massage local path
        orig_local = local
        if not is_file_like:
            local = os.path.abspath(local)
            if local != orig_local:
                debug(
                    "Massaged relative local path {!r} into {!r}".format(
                        orig_local, local
                    )
                )  # noqa

        # Run Paramiko-level .put() (side-effects only. womp.)
        # TODO: push some of the path handling into Paramiko; it should be
        # responsible for dealing with path cleaning etc.
        # TODO: probably preserve warning message from v1 when overwriting
        # existing files. Use logging for that obviously.
        #
        # If local appears to be a file-like object, use sftp.putfo, not put
        if is_file_like:
            msg = "Uploading file-like object {!r} to {!r}"
            debug(msg.format(local, remote))
            pointer = local.tell()
            try:
                local.seek(0)
                sftp.putfo(fl=local, remotepath=remote)
            finally:
                local.seek(pointer)
        else:
            debug("Uploading {!r} to {!r}".format(local, remote))
            sftp.put(localpath=local, remotepath=remote)
            # Set mode to same as local end
            # TODO: Push this down into SFTPClient sometime (requires backwards
            # incompat release.)
            #
            if preserve_mode:
                local_mode = os.stat(local).st_mode
                mode = stat.S_IMODE(local_mode)
                sftp.chmod(remote, mode)
        # Return something useful
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )


class Result(object):
    """
    A container for information about the result of a file transfer.

    See individual attribute/method documentation below for details.

    .. note::
        Unlike similar classes such as `invoke.runners.Result` or
        `fabric.runners.Result` (which have a concept of "warn and return
        anyways on failure") this class has no useful truthiness behavior. If a
        file transfer fails, some exception will be raised, either an `OSError`
        or an error from within Paramiko.

    .. versionadded:: 2.0
    """
    # TODO: how does this differ from put vs get? field stating which? (feels
    # meh) distinct classes differing, for now, solely by name? (also meh)
    def __init__(self, local, orig_local, remote, orig_remote, connection):
        #: The local path the file was saved as, or the object it was saved
        #: into if a file-like object was given instead.
        #:
        #: If a string path, this value is massaged to be absolute; see
        #: `.orig_local` for the original argument value.
        self.local = local
        #: The original value given as the returning method's ``local``
        #: argument.
        self.orig_local = orig_local
        #: The remote path downloaded from. Massaged to be absolute; see
        #: `.orig_remote` for the original argument value.
        self.remote = remote
        #: The original argument value given as the returning method's
        #: ``remote`` argument.
        self.orig_remote = orig_remote
        #: The `.Connection` object this result was obtained from.
        self.connection = connection

    # TODO: ensure str/repr makes it easily differentiable from run() or
    # local() result objects (and vice versa).
