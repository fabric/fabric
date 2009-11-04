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
Client-mode SFTP support.
"""

from binascii import hexlify
import errno
import os
import threading
import time
import weakref

from paramiko.sftp import *
from paramiko.sftp_attr import SFTPAttributes
from paramiko.ssh_exception import SSHException
from paramiko.sftp_file import SFTPFile


def _to_unicode(s):
    """
    decode a string as ascii or utf8 if possible (as required by the sftp
    protocol).  if neither works, just return a byte string because the server
    probably doesn't know the filename's encoding.
    """
    try:
        return s.encode('ascii')
    except UnicodeError:
        try:
            return s.decode('utf-8')
        except UnicodeError:
            return s


class SFTPClient (BaseSFTP):
    """
    SFTP client object.  C{SFTPClient} is used to open an sftp session across
    an open ssh L{Transport} and do remote file operations.
    """

    def __init__(self, sock):
        """
        Create an SFTP client from an existing L{Channel}.  The channel
        should already have requested the C{"sftp"} subsystem.

        An alternate way to create an SFTP client context is by using
        L{from_transport}.

        @param sock: an open L{Channel} using the C{"sftp"} subsystem
        @type sock: L{Channel}

        @raise SSHException: if there's an exception while negotiating
            sftp
        """
        BaseSFTP.__init__(self)
        self.sock = sock
        self.ultra_debug = False
        self.request_number = 1
        # lock for request_number
        self._lock = threading.Lock()
        self._cwd = None
        # request # -> SFTPFile
        self._expecting = weakref.WeakValueDictionary()
        if type(sock) is Channel:
            # override default logger
            transport = self.sock.get_transport()
            self.logger = util.get_logger(transport.get_log_channel() + '.sftp')
            self.ultra_debug = transport.get_hexdump()
        try:
            server_version = self._send_version()
        except EOFError, x:
            raise SSHException('EOF during negotiation')
        self._log(INFO, 'Opened sftp connection (server version %d)' % server_version)

    def from_transport(cls, t):
        """
        Create an SFTP client channel from an open L{Transport}.

        @param t: an open L{Transport} which is already authenticated
        @type t: L{Transport}
        @return: a new L{SFTPClient} object, referring to an sftp session
            (channel) across the transport
        @rtype: L{SFTPClient}
        """
        chan = t.open_session()
        if chan is None:
            return None
        chan.invoke_subsystem('sftp')
        return cls(chan)
    from_transport = classmethod(from_transport)
    
    def _log(self, level, msg, *args):
        super(SFTPClient, self)._log(level, "[chan %s] " + msg, *([ self.sock.get_name() ] + list(args)))

    def close(self):
        """
        Close the SFTP session and its underlying channel.
        
        @since: 1.4
        """
        self._log(INFO, 'sftp session closed.')
        self.sock.close()
    
    def get_channel(self):
        """
        Return the underlying L{Channel} object for this SFTP session.  This
        might be useful for doing things like setting a timeout on the channel.
        
        @return: the SSH channel
        @rtype: L{Channel}
        
        @since: 1.7.1
        """
        return self.sock

    def listdir(self, path='.'):
        """
        Return a list containing the names of the entries in the given C{path}.
        The list is in arbitrary order.  It does not include the special
        entries C{'.'} and C{'..'} even if they are present in the folder.
        This method is meant to mirror C{os.listdir} as closely as possible.
        For a list of full L{SFTPAttributes} objects, see L{listdir_attr}.

        @param path: path to list (defaults to C{'.'})
        @type path: str
        @return: list of filenames
        @rtype: list of str
        """
        return [f.filename for f in self.listdir_attr(path)]
        
    def listdir_attr(self, path='.'):
        """
        Return a list containing L{SFTPAttributes} objects corresponding to
        files in the given C{path}.  The list is in arbitrary order.  It does
        not include the special entries C{'.'} and C{'..'} even if they are
        present in the folder.
        
        The returned L{SFTPAttributes} objects will each have an additional
        field: C{longname}, which may contain a formatted string of the file's
        attributes, in unix format.  The content of this string will probably
        depend on the SFTP server implementation.

        @param path: path to list (defaults to C{'.'})
        @type path: str
        @return: list of attributes
        @rtype: list of L{SFTPAttributes}
        
        @since: 1.2
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'listdir(%r)' % path)
        t, msg = self._request(CMD_OPENDIR, path)
        if t != CMD_HANDLE:
            raise SFTPError('Expected handle')
        handle = msg.get_string()
        filelist = []
        while True:
            try:
                t, msg = self._request(CMD_READDIR, handle)
            except EOFError, e:
                # done with handle
                break
            if t != CMD_NAME:
                raise SFTPError('Expected name response')
            count = msg.get_int()
            for i in range(count):
                filename = _to_unicode(msg.get_string())
                longname = _to_unicode(msg.get_string())
                attr = SFTPAttributes._from_msg(msg, filename, longname)
                if (filename != '.') and (filename != '..'):
                    filelist.append(attr)
        self._request(CMD_CLOSE, handle)
        return filelist

    def open(self, filename, mode='r', bufsize=-1):
        """
        Open a file on the remote server.  The arguments are the same as for
        python's built-in C{file} (aka C{open}).  A file-like object is
        returned, which closely mimics the behavior of a normal python file
        object.

        The mode indicates how the file is to be opened: C{'r'} for reading,
        C{'w'} for writing (truncating an existing file), C{'a'} for appending,
        C{'r+'} for reading/writing, C{'w+'} for reading/writing (truncating an
        existing file), C{'a+'} for reading/appending.  The python C{'b'} flag
        is ignored, since SSH treats all files as binary.  The C{'U'} flag is
        supported in a compatible way.
        
        Since 1.5.2, an C{'x'} flag indicates that the operation should only
        succeed if the file was created and did not previously exist.  This has
        no direct mapping to python's file flags, but is commonly known as the
        C{O_EXCL} flag in posix.

        The file will be buffered in standard python style by default, but
        can be altered with the C{bufsize} parameter.  C{0} turns off
        buffering, C{1} uses line buffering, and any number greater than 1
        (C{>1}) uses that specific buffer size.

        @param filename: name of the file to open
        @type filename: str
        @param mode: mode (python-style) to open in
        @type mode: str
        @param bufsize: desired buffering (-1 = default buffer size)
        @type bufsize: int
        @return: a file object representing the open file
        @rtype: SFTPFile

        @raise IOError: if the file could not be opened.
        """
        filename = self._adjust_cwd(filename)
        self._log(DEBUG, 'open(%r, %r)' % (filename, mode))
        imode = 0
        if ('r' in mode) or ('+' in mode):
            imode |= SFTP_FLAG_READ
        if ('w' in mode) or ('+' in mode) or ('a' in mode):
            imode |= SFTP_FLAG_WRITE
        if ('w' in mode):
            imode |= SFTP_FLAG_CREATE | SFTP_FLAG_TRUNC
        if ('a' in mode):
            imode |= SFTP_FLAG_CREATE | SFTP_FLAG_APPEND
        if ('x' in mode):
            imode |= SFTP_FLAG_CREATE | SFTP_FLAG_EXCL
        attrblock = SFTPAttributes()
        t, msg = self._request(CMD_OPEN, filename, imode, attrblock)
        if t != CMD_HANDLE:
            raise SFTPError('Expected handle')
        handle = msg.get_string()
        self._log(DEBUG, 'open(%r, %r) -> %s' % (filename, mode, hexlify(handle)))
        return SFTPFile(self, handle, mode, bufsize)

    # python continues to vacillate about "open" vs "file"...
    file = open

    def remove(self, path):
        """
        Remove the file at the given path.  This only works on files; for
        removing folders (directories), use L{rmdir}.

        @param path: path (absolute or relative) of the file to remove
        @type path: str

        @raise IOError: if the path refers to a folder (directory)
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'remove(%r)' % path)
        self._request(CMD_REMOVE, path)

    unlink = remove

    def rename(self, oldpath, newpath):
        """
        Rename a file or folder from C{oldpath} to C{newpath}.

        @param oldpath: existing name of the file or folder
        @type oldpath: str
        @param newpath: new name for the file or folder
        @type newpath: str
        
        @raise IOError: if C{newpath} is a folder, or something else goes
            wrong
        """
        oldpath = self._adjust_cwd(oldpath)
        newpath = self._adjust_cwd(newpath)
        self._log(DEBUG, 'rename(%r, %r)' % (oldpath, newpath))
        self._request(CMD_RENAME, oldpath, newpath)

    def mkdir(self, path, mode=0777):
        """
        Create a folder (directory) named C{path} with numeric mode C{mode}.
        The default mode is 0777 (octal).  On some systems, mode is ignored.
        Where it is used, the current umask value is first masked out.

        @param path: name of the folder to create
        @type path: str
        @param mode: permissions (posix-style) for the newly-created folder
        @type mode: int
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'mkdir(%r, %r)' % (path, mode))
        attr = SFTPAttributes()
        attr.st_mode = mode
        self._request(CMD_MKDIR, path, attr)

    def rmdir(self, path):
        """
        Remove the folder named C{path}.

        @param path: name of the folder to remove
        @type path: str
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'rmdir(%r)' % path)
        self._request(CMD_RMDIR, path)

    def stat(self, path):
        """
        Retrieve information about a file on the remote system.  The return
        value is an object whose attributes correspond to the attributes of
        python's C{stat} structure as returned by C{os.stat}, except that it
        contains fewer fields.  An SFTP server may return as much or as little
        info as it wants, so the results may vary from server to server.

        Unlike a python C{stat} object, the result may not be accessed as a
        tuple.  This is mostly due to the author's slack factor.

        The fields supported are: C{st_mode}, C{st_size}, C{st_uid}, C{st_gid},
        C{st_atime}, and C{st_mtime}.

        @param path: the filename to stat
        @type path: str
        @return: an object containing attributes about the given file
        @rtype: SFTPAttributes
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'stat(%r)' % path)
        t, msg = self._request(CMD_STAT, path)
        if t != CMD_ATTRS:
            raise SFTPError('Expected attributes')
        return SFTPAttributes._from_msg(msg)

    def lstat(self, path):
        """
        Retrieve information about a file on the remote system, without
        following symbolic links (shortcuts).  This otherwise behaves exactly
        the same as L{stat}.

        @param path: the filename to stat
        @type path: str
        @return: an object containing attributes about the given file
        @rtype: SFTPAttributes
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'lstat(%r)' % path)
        t, msg = self._request(CMD_LSTAT, path)
        if t != CMD_ATTRS:
            raise SFTPError('Expected attributes')
        return SFTPAttributes._from_msg(msg)

    def symlink(self, source, dest):
        """
        Create a symbolic link (shortcut) of the C{source} path at
        C{destination}.

        @param source: path of the original file
        @type source: str
        @param dest: path of the newly created symlink
        @type dest: str
        """
        dest = self._adjust_cwd(dest)
        self._log(DEBUG, 'symlink(%r, %r)' % (source, dest))
        if type(source) is unicode:
            source = source.encode('utf-8')
        self._request(CMD_SYMLINK, source, dest)

    def chmod(self, path, mode):
        """
        Change the mode (permissions) of a file.  The permissions are
        unix-style and identical to those used by python's C{os.chmod}
        function.

        @param path: path of the file to change the permissions of
        @type path: str
        @param mode: new permissions
        @type mode: int
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'chmod(%r, %r)' % (path, mode))
        attr = SFTPAttributes()
        attr.st_mode = mode
        self._request(CMD_SETSTAT, path, attr)
        
    def chown(self, path, uid, gid):
        """
        Change the owner (C{uid}) and group (C{gid}) of a file.  As with
        python's C{os.chown} function, you must pass both arguments, so if you
        only want to change one, use L{stat} first to retrieve the current
        owner and group.

        @param path: path of the file to change the owner and group of
        @type path: str
        @param uid: new owner's uid
        @type uid: int
        @param gid: new group id
        @type gid: int
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'chown(%r, %r, %r)' % (path, uid, gid))
        attr = SFTPAttributes()
        attr.st_uid, attr.st_gid = uid, gid
        self._request(CMD_SETSTAT, path, attr)

    def utime(self, path, times):
        """
        Set the access and modified times of the file specified by C{path}.  If
        C{times} is C{None}, then the file's access and modified times are set
        to the current time.  Otherwise, C{times} must be a 2-tuple of numbers,
        of the form C{(atime, mtime)}, which is used to set the access and
        modified times, respectively.  This bizarre API is mimicked from python
        for the sake of consistency -- I apologize.

        @param path: path of the file to modify
        @type path: str
        @param times: C{None} or a tuple of (access time, modified time) in
            standard internet epoch time (seconds since 01 January 1970 GMT)
        @type times: tuple(int)
        """
        path = self._adjust_cwd(path)
        if times is None:
            times = (time.time(), time.time())
        self._log(DEBUG, 'utime(%r, %r)' % (path, times))
        attr = SFTPAttributes()
        attr.st_atime, attr.st_mtime = times
        self._request(CMD_SETSTAT, path, attr)

    def truncate(self, path, size):
        """
        Change the size of the file specified by C{path}.  This usually extends
        or shrinks the size of the file, just like the C{truncate()} method on
        python file objects.
        
        @param path: path of the file to modify
        @type path: str
        @param size: the new size of the file
        @type size: int or long
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'truncate(%r, %r)' % (path, size))
        attr = SFTPAttributes()
        attr.st_size = size
        self._request(CMD_SETSTAT, path, attr)

    def readlink(self, path):
        """
        Return the target of a symbolic link (shortcut).  You can use
        L{symlink} to create these.  The result may be either an absolute or
        relative pathname.

        @param path: path of the symbolic link file
        @type path: str
        @return: target path
        @rtype: str
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'readlink(%r)' % path)
        t, msg = self._request(CMD_READLINK, path)
        if t != CMD_NAME:
            raise SFTPError('Expected name response')
        count = msg.get_int()
        if count == 0:
            return None
        if count != 1:
            raise SFTPError('Readlink returned %d results' % count)
        return _to_unicode(msg.get_string())

    def normalize(self, path):
        """
        Return the normalized path (on the server) of a given path.  This
        can be used to quickly resolve symbolic links or determine what the
        server is considering to be the "current folder" (by passing C{'.'}
        as C{path}).

        @param path: path to be normalized
        @type path: str
        @return: normalized form of the given path
        @rtype: str
        
        @raise IOError: if the path can't be resolved on the server
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, 'normalize(%r)' % path)
        t, msg = self._request(CMD_REALPATH, path)
        if t != CMD_NAME:
            raise SFTPError('Expected name response')
        count = msg.get_int()
        if count != 1:
            raise SFTPError('Realpath returned %d results' % count)
        return _to_unicode(msg.get_string())
    
    def chdir(self, path):
        """
        Change the "current directory" of this SFTP session.  Since SFTP
        doesn't really have the concept of a current working directory, this
        is emulated by paramiko.  Once you use this method to set a working
        directory, all operations on this SFTPClient object will be relative
        to that path.
        
        @param path: new current working directory
        @type path: str
        
        @raise IOError: if the requested path doesn't exist on the server
        
        @since: 1.4
        """
        self._cwd = self.normalize(path)
    
    def getcwd(self):
        """
        Return the "current working directory" for this SFTP session, as
        emulated by paramiko.  If no directory has been set with L{chdir},
        this method will return C{None}.
        
        @return: the current working directory on the server, or C{None}
        @rtype: str
        
        @since: 1.4
        """
        return self._cwd
    
    def put(self, localpath, remotepath, callback=None):
        """
        Copy a local file (C{localpath}) to the SFTP server as C{remotepath}.
        Any exception raised by operations will be passed through.  This
        method is primarily provided as a convenience.
        
        The SFTP operations use pipelining for speed.
        
        @param localpath: the local file to copy
        @type localpath: str
        @param remotepath: the destination path on the SFTP server
        @type remotepath: str
        @param callback: optional callback function that accepts the bytes
            transferred so far and the total bytes to be transferred
            (since 1.7.4)
        @type callback: function(int, int)
        @return: an object containing attributes about the given file
            (since 1.7.4)
        @rtype: SFTPAttributes
        
        @since: 1.4
        """
        file_size = os.stat(localpath).st_size
        fl = file(localpath, 'rb')
        fr = self.file(remotepath, 'wb')
        fr.set_pipelined(True)
        size = 0
        while True:
            data = fl.read(32768)
            if len(data) == 0:
                break
            fr.write(data)
            size += len(data)
            if callback is not None:
                callback(size, file_size)
        fl.close()
        fr.close()
        s = self.stat(remotepath)
        if s.st_size != size:
            raise IOError('size mismatch in put!  %d != %d' % (s.st_size, size))
        return s
    
    def get(self, remotepath, localpath, callback=None):
        """
        Copy a remote file (C{remotepath}) from the SFTP server to the local
        host as C{localpath}.  Any exception raised by operations will be
        passed through.  This method is primarily provided as a convenience.
        
        @param remotepath: the remote file to copy
        @type remotepath: str
        @param localpath: the destination path on the local host
        @type localpath: str
        @param callback: optional callback function that accepts the bytes
            transferred so far and the total bytes to be transferred
            (since 1.7.4)
        @type callback: function(int, int)
        
        @since: 1.4
        """
        fr = self.file(remotepath, 'rb')
        file_size = self.stat(remotepath).st_size
        fr.prefetch()
        fl = file(localpath, 'wb')
        size = 0
        while True:
            data = fr.read(32768)
            if len(data) == 0:
                break
            fl.write(data)
            size += len(data)
            if callback is not None:
                callback(size, file_size)
        fl.close()
        fr.close()
        s = os.stat(localpath)
        if s.st_size != size:
            raise IOError('size mismatch in get!  %d != %d' % (s.st_size, size))


    ###  internals...


    def _request(self, t, *arg):
        num = self._async_request(type(None), t, *arg)
        return self._read_response(num)
    
    def _async_request(self, fileobj, t, *arg):
        # this method may be called from other threads (prefetch)
        self._lock.acquire()
        try:
            msg = Message()
            msg.add_int(self.request_number)
            for item in arg:
                if type(item) is int:
                    msg.add_int(item)
                elif type(item) is long:
                    msg.add_int64(item)
                elif type(item) is str:
                    msg.add_string(item)
                elif type(item) is SFTPAttributes:
                    item._pack(msg)
                else:
                    raise Exception('unknown type for %r type %r' % (item, type(item)))
            num = self.request_number
            self._expecting[num] = fileobj
            self._send_packet(t, str(msg))
            self.request_number += 1
        finally:
            self._lock.release()
        return num

    def _read_response(self, waitfor=None):
        while True:
            try:
                t, data = self._read_packet()
            except EOFError, e:
                raise SSHException('Server connection dropped: %s' % (str(e),))
            msg = Message(data)
            num = msg.get_int()
            if num not in self._expecting:
                # might be response for a file that was closed before responses came back
                self._log(DEBUG, 'Unexpected response #%d' % (num,))
                if waitfor is None:
                    # just doing a single check
                    break
                continue
            fileobj = self._expecting[num]
            del self._expecting[num]
            if num == waitfor:
                # synchronous
                if t == CMD_STATUS:
                    self._convert_status(msg)
                return t, msg
            if fileobj is not type(None):
                fileobj._async_response(t, msg)
            if waitfor is None:
                # just doing a single check
                break
        return (None, None)

    def _finish_responses(self, fileobj):
        while fileobj in self._expecting.values():
            self._read_response()
            fileobj._check_exception()

    def _convert_status(self, msg):
        """
        Raises EOFError or IOError on error status; otherwise does nothing.
        """
        code = msg.get_int()
        text = msg.get_string()
        if code == SFTP_OK:
            return
        elif code == SFTP_EOF:
            raise EOFError(text)
        elif code == SFTP_NO_SUCH_FILE:
            # clever idea from john a. meinel: map the error codes to errno
            raise IOError(errno.ENOENT, text)
        elif code == SFTP_PERMISSION_DENIED:
            raise IOError(errno.EACCES, text)
        else:
            raise IOError(text)
    
    def _adjust_cwd(self, path):
        """
        Return an adjusted path if we're emulating a "current working
        directory" for the server.
        """
        if type(path) is unicode:
            path = path.encode('utf-8')
        if self._cwd is None:
            return path
        if (len(path) > 0) and (path[0] == '/'):
            # absolute path
            return path
        if self._cwd == '/':
            return self._cwd + path
        return self._cwd + '/' + path


class SFTP (SFTPClient):
    "an alias for L{SFTPClient} for backwards compatability"
    pass
