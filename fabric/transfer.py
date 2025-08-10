"""
File transfer via SFTP and/or SCP.
"""

import os
import posixpath
import stat

from pathlib import Path

from .util import debug  # TODO: actual logging! LOL

# TODO: figure out best way to direct folks seeking rsync, to patchwork's rsync
# call (which needs updating to use invoke.run() & fab 2 connection methods,
# but is otherwise suitable).
# UNLESS we want to try and shoehorn it into this module after all? Delegate
# any recursive get/put to it? Requires users to have rsync available of
# course.


class Transfer:
    """
    `.Connection`-wrapping class responsible for managing file upload/download.

    .. versionadded:: 2.0
    """

    # TODO: SFTP clear default, but how to do SCP? subclass? init kwarg?

    def __init__(self, connection):
        self.connection = connection

    def sftp(self, subsystem=None):
        return self.connection.sftp(subsystem)

    def is_remote_dir(self, path, subsystem=None):
        try:
            return stat.S_ISDIR(self.sftp(subsystem).stat(path).st_mode)
        except IOError:
            return False

    def get(self, remote, local=None, preserve_mode=True, subsystem=None):
        """
        Copy a file from wrapped connection's host to the local filesystem.

        :param str remote:
            Remote file to download.

            May be absolute, or relative to the remote working directory.

            .. note::
                Most SFTP servers set the remote working directory to the
                connecting user's home directory, and (unlike most shells) do
                *not* expand tildes (``~``).

                For example, instead of saying ``get("~/tmp/archive.tgz")``,
                say ``get("tmp/archive.tgz")``.

        :param local:
            Local path to store downloaded file in, or a file-like object.

            **If None or another 'falsey'/empty value is given** (the default),
            the remote file is downloaded to the current working directory (as
            seen by `os.getcwd`) using its remote filename. (This is equivalent
            to giving ``"{basename}"``; see the below subsection on
            interpolation.)

            **If a string is given**, it should be a path to a local directory
            or file and is subject to similar behavior as that seen by common
            Unix utilities or OpenSSH's ``sftp`` or ``scp`` tools.

            For example, if the local path is a directory, the remote path's
            base filename will be added onto it (so ``get('foo/bar/file.txt',
            '/tmp/')`` would result in creation or overwriting of
            ``/tmp/file.txt``).

            This path will be **interpolated** with some useful parameters,
            using `str.format`:

            - The `.Connection` object's ``host``, ``user`` and ``port``
              attributes.
            - The ``basename`` and ``dirname`` of the ``remote`` path, as
              derived by `os.path` (specifically, its ``posixpath`` flavor, so
              that the resulting values are useful on remote POSIX-compatible
              SFTP servers even if the local client is Windows).
            - Thus, for example, ``"/some/path/{user}@{host}/{basename}"`` will
              yield different local paths depending on the properties of both
              the connection and the remote path.

            .. note::
                If nonexistent directories are present in this path (including
                the final path component, if it ends in `os.sep`) they will be
                created automatically using `os.makedirs`.

            **If a file-like object is given**, the contents of the remote file
            are simply written into it.

        :param bool preserve_mode:
            Whether to `os.chmod` the local file so it matches the remote
            file's mode (default: ``True``).

        :param bool subsystem:
            Specifies an sftp subsystem to use, e.g.
            ``/usr/bin/sudo /usr/lib/openssh/sftp-server``
            will allow files to be gotten as the root user.
            If ``None``, use the default subsystem.

        :returns: A `.Result` object.

        .. versionadded:: 2.0
        .. versionchanged:: 2.6
            Added ``local`` path interpolation of connection & remote file
            attributes.
        .. versionchanged:: 2.6
            Create missing ``local`` directories automatically.
        """
        # TODO: how does this API change if we want to implement
        # remote-to-remote file transfer? (Is that even realistic?)
        # TODO: callback support
        # TODO: how best to allow changing the behavior/semantics of
        # remote/local (e.g. users might want 'safer' behavior that complains
        # instead of overwriting existing files) - this likely ties into the
        # "how to handle recursive/rsync" and "how to handle scp" questions

        # Massage remote path
        if not remote:
            raise ValueError("Remote path must not be empty!")
        orig_remote = remote
        remote = posixpath.join(
            self.sftp(subsystem).getcwd()
            or self.sftp(subsystem).normalize("."),
            remote,
        )

        # Massage local path
        orig_local = local
        is_file_like = hasattr(local, "write") and callable(local.write)
        remote_filename = posixpath.basename(remote)
        if not local:
            local = remote_filename
        # Path-driven local downloads need interpolation, abspath'ing &
        # directory creation
        if not is_file_like:
            local = local.format(
                host=self.connection.host,
                user=self.connection.user,
                port=self.connection.port,
                dirname=posixpath.dirname(remote),
                basename=remote_filename,
            )
            # Must treat dir vs file paths differently, lest we erroneously
            # mkdir what was intended as a filename, and so that non-empty
            # dir-like paths still get remote filename tacked on.
            if local.endswith(os.sep):
                dir_path = local
                local = os.path.join(local, remote_filename)
            else:
                dir_path, _ = os.path.split(local)
            local = os.path.abspath(local)
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            # TODO: reimplement mkdir (or otherwise write a testing function)
            # allowing us to track what was created so we can revert if
            # transfer fails.
            # TODO: Alternately, transfer to temp location and then move, but
            # that's basically inverse of v1's sudo-put which gets messy

        # Run Paramiko-level .get() (side-effects only. womp.)
        # TODO: push some of the path handling into Paramiko; it should be
        # responsible for dealing with path cleaning etc.
        # TODO: probably preserve warning message from v1 when overwriting
        # existing files. Use logging for that obviously.
        #
        # If local appears to be a file-like object, use sftp.getfo, not get
        if is_file_like:
            self.sftp(subsystem).getfo(remotepath=remote, fl=local)
        else:
            self.sftp(subsystem).get(remotepath=remote, localpath=local)
            # Set mode to same as remote end
            # TODO: Push this down into SFTPClient sometime (requires backwards
            # incompat release.)
            if preserve_mode:
                remote_mode = self.sftp(subsystem).stat(remote).st_mode
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

    def put(self, local, remote=None, preserve_mode=True, subsystem=None):
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
            Remote path to which the local file will be written.

            .. note::
                Most SFTP servers set the remote working directory to the
                connecting user's home directory, and (unlike most shells) do
                *not* expand tildes (``~``).

                For example, instead of saying ``put("archive.tgz",
                "~/tmp/")``, say ``put("archive.tgz", "tmp/")``.

                In addition, this means that 'falsey'/empty values (such as the
                default value, ``None``) are allowed and result in uploading to
                the remote home directory.

            .. note::
                When ``local`` is a file-like object, ``remote`` is required
                and must refer to a valid file path (not a directory).

        :param bool preserve_mode:
            Whether to ``chmod`` the remote file so it matches the local file's
            mode (default: ``True``).

        :param bool subsystem:
            Specifies an sftp subsystem to use, e.g.
            ``/usr/bin/sudo /usr/lib/openssh/sftp-server``
            will allow files to be put as the root user.
            If ``None``, use the default subsystem.

        :returns: A `.Result` object.

        .. versionadded:: 2.0
        """
        if not local:
            raise ValueError("Local path must not be empty!")

        is_file_like = hasattr(local, "write") and callable(local.write)

        # Massage remote path
        orig_remote = remote
        if is_file_like:
            local_base = getattr(local, "name", None)
        else:
            local_base = os.path.basename(local)
        if not remote:
            if is_file_like:
                raise ValueError(
                    "Must give non-empty remote path when local is a file-like object!"  # noqa
                )
            else:
                remote = local_base
                debug("Massaged empty remote path into {!r}".format(remote))
        elif self.is_remote_dir(remote, subsystem):
            # non-empty local_base implies a) text file path or b) FLO which
            # had a non-empty .name attribute. huzzah!
            if local_base:
                remote = posixpath.join(remote, local_base)
            else:
                if is_file_like:
                    raise ValueError(
                        "Can't put a file-like-object into a directory unless it has a non-empty .name attribute!"  # noqa
                    )
                else:
                    # TODO: can we ever really end up here? implies we want to
                    # reorganize all this logic so it has fewer potential holes
                    raise ValueError(
                        "Somehow got an empty local file basename ({!r}) when uploading to a directory ({!r})!".format(  # noqa
                            local_base, remote
                        )
                    )

        prejoined_remote = remote
        remote = posixpath.join(
            self.sftp(subsystem).getcwd()
            or self.sftp(subsystem).normalize("."),
            remote,
        )
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
                self.sftp(subsystem).putfo(fl=local, remotepath=remote)
            finally:
                local.seek(pointer)
        else:
            debug("Uploading {!r} to {!r}".format(local, remote))
            self.sftp(subsystem).put(localpath=local, remotepath=remote)
            # Set mode to same as local end
            # TODO: Push this down into SFTPClient sometime (requires backwards
            # incompat release.)
            if preserve_mode:
                local_mode = os.stat(local).st_mode
                mode = stat.S_IMODE(local_mode)
                self.sftp(subsystem).chmod(remote, mode)
        # Return something useful
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )


class Result:
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
