"""
File transfer via SFTP and/or SCP.
"""

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

    def get(self, remote, local=None):
        """
        Download a file from the current connection to the local filesystem.

        :param str remote:
            Remote file to download.

            Must evaluate to a file (not a directory). May be relative (from
            remote default CWD, typically connecting user's ``$HOME``) or
            absolute.

        :param str local:
            Local path to store downloaded file in, or a file-like object.

            **If ``None`` is given** (the default), the remote file is
            downloaded to the current working directory (as seen by `os.cwd`)
            using its remote filename.

            **If a string is given**, it should be a path to a local directory
            or file and is subject to similar behavior as that seen by common
            Unix utilities or OpenSSH's ``sftp`` or ``scp`` tools. For example,
            if the local path is a directory, the remote path's base filename
            will be added onto it (so ``get('foo/bar/file.txt', '/tmp/')``
            would result in creation or overwriting of ``/tmp/file.txt``).

            .. note::
                When dealing with nonexistent file paths, normal Python file
                handling concerns will be present - for example, a local path
                containing non-leaf directories which do not exist, will
                typically result in an `OSError`.

            **If a file-like object is given**, the contents of the remote file
            are simply written into it.

            .. note::
                The file-like object will be 'rewound' to the beginning using
                `file.seek` to ensure a clean write.

        :returns: A `.Result` object.
        """
        # TODO: how does this API change if we want to implement
        # remote-to-remote file transfer?
        # TODO: handle v1's string interpolation bits, especially the default
        # one, or at least think about how that would work re: split between
        # single and multiple server targets.
        # TODO: callback support
        #
        sftp = self.connection.sftp()
        sftp.get(remotepath=remote, localpath=local)
        return Result(remote=remote, local=local)


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
    def __init__(self, local, remote):
        #: The local path the file was saved as, or ``None`` if a file-like
        #: object was given instead.
        self.local = local
        #: The remote path downloaded from.
        self.remote = remote
