# Copyright (C) 2003-2007  Robey Pointer <robey@lag.net>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
L{SFTPServerInterface} is an interface to override for SFTP server support.
"""

import os

from paramiko.common import *
from paramiko.sftp import *


class SFTPServerInterface (object):
    """
    This class defines an interface for controlling the behavior of paramiko
    when using the L{SFTPServer} subsystem to provide an SFTP server.

    Methods on this class are called from the SFTP session's thread, so you can
    block as long as necessary without affecting other sessions (even other
    SFTP sessions).  However, raising an exception will usually cause the SFTP
    session to abruptly end, so you will usually want to catch exceptions and
    return an appropriate error code.
    
    All paths are in string form instead of unicode because not all SFTP
    clients & servers obey the requirement that paths be encoded in UTF-8.
    """
    
    def __init__ (self, server, *largs, **kwargs):
        """
        Create a new SFTPServerInterface object.  This method does nothing by
        default and is meant to be overridden by subclasses.
        
        @param server: the server object associated with this channel and
            SFTP subsystem
        @type server: L{ServerInterface}
        """
        super(SFTPServerInterface, self).__init__(*largs, **kwargs)

    def session_started(self):
        """
        The SFTP server session has just started.  This method is meant to be
        overridden to perform any necessary setup before handling callbacks
        from SFTP operations.
        """
        pass

    def session_ended(self):
        """
        The SFTP server session has just ended, either cleanly or via an
        exception.  This method is meant to be overridden to perform any
        necessary cleanup before this C{SFTPServerInterface} object is
        destroyed.
        """
        pass

    def open(self, path, flags, attr):
        """
        Open a file on the server and create a handle for future operations
        on that file.  On success, a new object subclassed from L{SFTPHandle}
        should be returned.  This handle will be used for future operations
        on the file (read, write, etc).  On failure, an error code such as
        L{SFTP_PERMISSION_DENIED} should be returned.

        C{flags} contains the requested mode for opening (read-only,
        write-append, etc) as a bitset of flags from the C{os} module:
            - C{os.O_RDONLY}
            - C{os.O_WRONLY}
            - C{os.O_RDWR}
            - C{os.O_APPEND}
            - C{os.O_CREAT}
            - C{os.O_TRUNC}
            - C{os.O_EXCL}
        (One of C{os.O_RDONLY}, C{os.O_WRONLY}, or C{os.O_RDWR} will always
        be set.)

        The C{attr} object contains requested attributes of the file if it
        has to be created.  Some or all attribute fields may be missing if
        the client didn't specify them.
        
        @note: The SFTP protocol defines all files to be in "binary" mode.
            There is no equivalent to python's "text" mode.

        @param path: the requested path (relative or absolute) of the file
            to be opened.
        @type path: str
        @param flags: flags or'd together from the C{os} module indicating the
            requested mode for opening the file.
        @type flags: int
        @param attr: requested attributes of the file if it is newly created.
        @type attr: L{SFTPAttributes}
        @return: a new L{SFTPHandle} I{or error code}.
        @rtype L{SFTPHandle}
        """
        return SFTP_OP_UNSUPPORTED

    def list_folder(self, path):
        """
        Return a list of files within a given folder.  The C{path} will use
        posix notation (C{"/"} separates folder names) and may be an absolute
        or relative path.

        The list of files is expected to be a list of L{SFTPAttributes}
        objects, which are similar in structure to the objects returned by
        C{os.stat}.  In addition, each object should have its C{filename}
        field filled in, since this is important to a directory listing and
        not normally present in C{os.stat} results.  The method
        L{SFTPAttributes.from_stat} will usually do what you want.

        In case of an error, you should return one of the C{SFTP_*} error
        codes, such as L{SFTP_PERMISSION_DENIED}.

        @param path: the requested path (relative or absolute) to be listed.
        @type path: str
        @return: a list of the files in the given folder, using
            L{SFTPAttributes} objects.
        @rtype: list of L{SFTPAttributes} I{or error code}
        
        @note: You should normalize the given C{path} first (see the
        C{os.path} module) and check appropriate permissions before returning
        the list of files.  Be careful of malicious clients attempting to use
        relative paths to escape restricted folders, if you're doing a direct
        translation from the SFTP server path to your local filesystem.
        """
        return SFTP_OP_UNSUPPORTED

    def stat(self, path):
        """
        Return an L{SFTPAttributes} object for a path on the server, or an
        error code.  If your server supports symbolic links (also known as
        "aliases"), you should follow them.  (L{lstat} is the corresponding
        call that doesn't follow symlinks/aliases.)

        @param path: the requested path (relative or absolute) to fetch
            file statistics for.
        @type path: str
        @return: an attributes object for the given file, or an SFTP error
            code (like L{SFTP_PERMISSION_DENIED}).
        @rtype: L{SFTPAttributes} I{or error code}
        """
        return SFTP_OP_UNSUPPORTED

    def lstat(self, path):
        """
        Return an L{SFTPAttributes} object for a path on the server, or an
        error code.  If your server supports symbolic links (also known as
        "aliases"), you should I{not} follow them -- instead, you should
        return data on the symlink or alias itself.  (L{stat} is the
        corresponding call that follows symlinks/aliases.)

        @param path: the requested path (relative or absolute) to fetch
            file statistics for.
        @type path: str
        @return: an attributes object for the given file, or an SFTP error
            code (like L{SFTP_PERMISSION_DENIED}).
        @rtype: L{SFTPAttributes} I{or error code}
        """
        return SFTP_OP_UNSUPPORTED

    def remove(self, path):
        """
        Delete a file, if possible.

        @param path: the requested path (relative or absolute) of the file
            to delete.
        @type path: str
        @return: an SFTP error code like L{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED

    def rename(self, oldpath, newpath):
        """
        Rename (or move) a file.  The SFTP specification implies that this
        method can be used to move an existing file into a different folder,
        and since there's no other (easy) way to move files via SFTP, it's
        probably a good idea to implement "move" in this method too, even for
        files that cross disk partition boundaries, if at all possible.
        
        @note: You should return an error if a file with the same name as
            C{newpath} already exists.  (The rename operation should be
            non-desctructive.)

        @param oldpath: the requested path (relative or absolute) of the
            existing file.
        @type oldpath: str
        @param newpath: the requested new path of the file.
        @type newpath: str
        @return: an SFTP error code like L{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED

    def mkdir(self, path, attr):
        """
        Create a new directory with the given attributes.  The C{attr}
        object may be considered a "hint" and ignored.

        The C{attr} object will contain only those fields provided by the
        client in its request, so you should use C{hasattr} to check for
        the presense of fields before using them.  In some cases, the C{attr}
        object may be completely empty.

        @param path: requested path (relative or absolute) of the new
            folder.
        @type path: str
        @param attr: requested attributes of the new folder.
        @type attr: L{SFTPAttributes}
        @return: an SFTP error code like L{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED

    def rmdir(self, path):
        """
        Remove a directory if it exists.  The C{path} should refer to an
        existing, empty folder -- otherwise this method should return an
        error.

        @param path: requested path (relative or absolute) of the folder
            to remove.
        @type path: str
        @return: an SFTP error code like L{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED

    def chattr(self, path, attr):
        """
        Change the attributes of a file.  The C{attr} object will contain
        only those fields provided by the client in its request, so you
        should check for the presence of fields before using them.

        @param path: requested path (relative or absolute) of the file to
            change.
        @type path: str
        @param attr: requested attributes to change on the file.
        @type attr: L{SFTPAttributes}
        @return: an error code like L{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED

    def canonicalize(self, path):
        """
        Return the canonical form of a path on the server.  For example,
        if the server's home folder is C{/home/foo}, the path
        C{"../betty"} would be canonicalized to C{"/home/betty"}.  Note
        the obvious security issues: if you're serving files only from a
        specific folder, you probably don't want this method to reveal path
        names outside that folder.

        You may find the python methods in C{os.path} useful, especially
        C{os.path.normpath} and C{os.path.realpath}.

        The default implementation returns C{os.path.normpath('/' + path)}.
        """
        if os.path.isabs(path):
            out = os.path.normpath(path)
        else:
            out = os.path.normpath('/' + path)
        if sys.platform == 'win32':
            # on windows, normalize backslashes to sftp/posix format
            out = out.replace('\\', '/')
        return out
    
    def readlink(self, path):
        """
        Return the target of a symbolic link (or shortcut) on the server.
        If the specified path doesn't refer to a symbolic link, an error
        should be returned.
        
        @param path: path (relative or absolute) of the symbolic link.
        @type path: str
        @return: the target path of the symbolic link, or an error code like
            L{SFTP_NO_SUCH_FILE}.
        @rtype: str I{or error code}
        """
        return SFTP_OP_UNSUPPORTED
    
    def symlink(self, target_path, path):
        """
        Create a symbolic link on the server, as new pathname C{path},
        with C{target_path} as the target of the link.
        
        @param target_path: path (relative or absolute) of the target for
            this new symbolic link.
        @type target_path: str
        @param path: path (relative or absolute) of the symbolic link to
            create.
        @type path: str
        @return: an error code like C{SFTP_OK}.
        @rtype: int
        """
        return SFTP_OP_UNSUPPORTED
