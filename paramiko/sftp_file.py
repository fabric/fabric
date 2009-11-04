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
L{SFTPFile}
"""

from binascii import hexlify
import socket
import threading
import time

from paramiko.common import *
from paramiko.sftp import *
from paramiko.file import BufferedFile
from paramiko.sftp_attr import SFTPAttributes


class SFTPFile (BufferedFile):
    """
    Proxy object for a file on the remote server, in client mode SFTP.
    """

    # Some sftp servers will choke if you send read/write requests larger than
    # this size.
    MAX_REQUEST_SIZE = 32768

    def __init__(self, sftp, handle, mode='r', bufsize=-1):
        BufferedFile.__init__(self)
        self.sftp = sftp
        self.handle = handle
        BufferedFile._set_mode(self, mode, bufsize)
        self.pipelined = False
        self._prefetching = False
        self._prefetch_done = False
        self._prefetch_data = {}
        self._prefetch_reads = []
        self._saved_exception = None

    def __del__(self):
        self._close(async=True)
    
    def close(self):
        self._close(async=False)
        
    def _close(self, async=False):
        # We allow double-close without signaling an error, because real
        # Python file objects do.  However, we must protect against actually
        # sending multiple CMD_CLOSE packets, because after we close our
        # handle, the same handle may be re-allocated by the server, and we
        # may end up mysteriously closing some random other file.  (This is
        # especially important because we unconditionally call close() from
        # __del__.)
        if self._closed:
            return
        self.sftp._log(DEBUG, 'close(%s)' % hexlify(self.handle))
        if self.pipelined:
            self.sftp._finish_responses(self)
        BufferedFile.close(self)
        try:
            if async:
                # GC'd file handle could be called from an arbitrary thread -- don't wait for a response
                self.sftp._async_request(type(None), CMD_CLOSE, self.handle)
            else:
                self.sftp._request(CMD_CLOSE, self.handle)
        except EOFError:
            # may have outlived the Transport connection
            pass
        except (IOError, socket.error):
            # may have outlived the Transport connection
            pass

    def _data_in_prefetch_requests(self, offset, size):
        k = [i for i in self._prefetch_reads if i[0] <= offset]
        if len(k) == 0:
            return False
        k.sort(lambda x, y: cmp(x[0], y[0]))
        buf_offset, buf_size = k[-1]
        if buf_offset + buf_size <= offset:
            # prefetch request ends before this one begins
            return False
        if buf_offset + buf_size >= offset + size:
            # inclusive
            return True
        # well, we have part of the request.  see if another chunk has the rest.
        return self._data_in_prefetch_requests(buf_offset + buf_size, offset + size - buf_offset - buf_size)
    
    def _data_in_prefetch_buffers(self, offset):
        """
        if a block of data is present in the prefetch buffers, at the given
        offset, return the offset of the relevant prefetch buffer.  otherwise,
        return None.  this guarantees nothing about the number of bytes
        collected in the prefetch buffer so far.
        """
        k = [i for i in self._prefetch_data.keys() if i <= offset]
        if len(k) == 0:
            return None
        index = max(k)
        buf_offset = offset - index
        if buf_offset >= len(self._prefetch_data[index]):
            # it's not here
            return None
        return index
        
    def _read_prefetch(self, size):
        """
        read data out of the prefetch buffer, if possible.  if the data isn't
        in the buffer, return None.  otherwise, behaves like a normal read.
        """
        # while not closed, and haven't fetched past the current position, and haven't reached EOF...
        while True:
            offset = self._data_in_prefetch_buffers(self._realpos)
            if offset is not None:
                break
            if self._prefetch_done or self._closed:
                break
            self.sftp._read_response()
            self._check_exception()
        if offset is None:
            self._prefetching = False
            return None
        prefetch = self._prefetch_data[offset]
        del self._prefetch_data[offset]
        
        buf_offset = self._realpos - offset
        if buf_offset > 0:
            self._prefetch_data[offset] = prefetch[:buf_offset]
            prefetch = prefetch[buf_offset:]
        if size < len(prefetch):
            self._prefetch_data[self._realpos + size] = prefetch[size:]
            prefetch = prefetch[:size]
        return prefetch
        
    def _read(self, size):
        size = min(size, self.MAX_REQUEST_SIZE)
        if self._prefetching:
            data = self._read_prefetch(size)
            if data is not None:
                return data
        t, msg = self.sftp._request(CMD_READ, self.handle, long(self._realpos), int(size))
        if t != CMD_DATA:
            raise SFTPError('Expected data')
        return msg.get_string()

    def _write(self, data):
        # may write less than requested if it would exceed max packet size
        chunk = min(len(data), self.MAX_REQUEST_SIZE)
        req = self.sftp._async_request(type(None), CMD_WRITE, self.handle, long(self._realpos), str(data[:chunk]))
        if not self.pipelined or self.sftp.sock.recv_ready():
            t, msg = self.sftp._read_response(req)
            if t != CMD_STATUS:
                raise SFTPError('Expected status')
            # convert_status already called
        return chunk

    def settimeout(self, timeout):
        """
        Set a timeout on read/write operations on the underlying socket or
        ssh L{Channel}.

        @see: L{Channel.settimeout}
        @param timeout: seconds to wait for a pending read/write operation
            before raising C{socket.timeout}, or C{None} for no timeout
        @type timeout: float
        """
        self.sftp.sock.settimeout(timeout)

    def gettimeout(self):
        """
        Returns the timeout in seconds (as a float) associated with the socket
        or ssh L{Channel} used for this file.

        @see: L{Channel.gettimeout}
        @rtype: float
        """
        return self.sftp.sock.gettimeout()

    def setblocking(self, blocking):
        """
        Set blocking or non-blocking mode on the underiying socket or ssh
        L{Channel}.

        @see: L{Channel.setblocking}
        @param blocking: 0 to set non-blocking mode; non-0 to set blocking
            mode.
        @type blocking: int
        """
        self.sftp.sock.setblocking(blocking)

    def seek(self, offset, whence=0):
        self.flush()
        if whence == self.SEEK_SET:
            self._realpos = self._pos = offset
        elif whence == self.SEEK_CUR:
            self._pos += offset
            self._realpos = self._pos
        else:
            self._realpos = self._pos = self._get_size() + offset
        self._rbuffer = ''

    def stat(self):
        """
        Retrieve information about this file from the remote system.  This is
        exactly like L{SFTP.stat}, except that it operates on an already-open
        file.

        @return: an object containing attributes about this file.
        @rtype: SFTPAttributes
        """
        t, msg = self.sftp._request(CMD_FSTAT, self.handle)
        if t != CMD_ATTRS:
            raise SFTPError('Expected attributes')
        return SFTPAttributes._from_msg(msg)

    def chmod(self, mode):
        """
        Change the mode (permissions) of this file.  The permissions are
        unix-style and identical to those used by python's C{os.chmod}
        function.

        @param mode: new permissions
        @type mode: int
        """
        self.sftp._log(DEBUG, 'chmod(%s, %r)' % (hexlify(self.handle), mode))
        attr = SFTPAttributes()
        attr.st_mode = mode
        self.sftp._request(CMD_FSETSTAT, self.handle, attr)
        
    def chown(self, uid, gid):
        """
        Change the owner (C{uid}) and group (C{gid}) of this file.  As with
        python's C{os.chown} function, you must pass both arguments, so if you
        only want to change one, use L{stat} first to retrieve the current
        owner and group.

        @param uid: new owner's uid
        @type uid: int
        @param gid: new group id
        @type gid: int
        """
        self.sftp._log(DEBUG, 'chown(%s, %r, %r)' % (hexlify(self.handle), uid, gid))
        attr = SFTPAttributes()
        attr.st_uid, attr.st_gid = uid, gid
        self.sftp._request(CMD_FSETSTAT, self.handle, attr)

    def utime(self, times):
        """
        Set the access and modified times of this file.  If
        C{times} is C{None}, then the file's access and modified times are set
        to the current time.  Otherwise, C{times} must be a 2-tuple of numbers,
        of the form C{(atime, mtime)}, which is used to set the access and
        modified times, respectively.  This bizarre API is mimicked from python
        for the sake of consistency -- I apologize.

        @param times: C{None} or a tuple of (access time, modified time) in
            standard internet epoch time (seconds since 01 January 1970 GMT)
        @type times: tuple(int)
        """
        if times is None:
            times = (time.time(), time.time())
        self.sftp._log(DEBUG, 'utime(%s, %r)' % (hexlify(self.handle), times))
        attr = SFTPAttributes()
        attr.st_atime, attr.st_mtime = times
        self.sftp._request(CMD_FSETSTAT, self.handle, attr)

    def truncate(self, size):
        """
        Change the size of this file.  This usually extends
        or shrinks the size of the file, just like the C{truncate()} method on
        python file objects.
        
        @param size: the new size of the file
        @type size: int or long
        """
        self.sftp._log(DEBUG, 'truncate(%s, %r)' % (hexlify(self.handle), size))
        attr = SFTPAttributes()
        attr.st_size = size
        self.sftp._request(CMD_FSETSTAT, self.handle, attr)
    
    def check(self, hash_algorithm, offset=0, length=0, block_size=0):
        """
        Ask the server for a hash of a section of this file.  This can be used
        to verify a successful upload or download, or for various rsync-like
        operations.
        
        The file is hashed from C{offset}, for C{length} bytes.  If C{length}
        is 0, the remainder of the file is hashed.  Thus, if both C{offset}
        and C{length} are zero, the entire file is hashed.
        
        Normally, C{block_size} will be 0 (the default), and this method will
        return a byte string representing the requested hash (for example, a
        string of length 16 for MD5, or 20 for SHA-1).  If a non-zero
        C{block_size} is given, each chunk of the file (from C{offset} to
        C{offset + length}) of C{block_size} bytes is computed as a separate
        hash.  The hash results are all concatenated and returned as a single
        string.
        
        For example, C{check('sha1', 0, 1024, 512)} will return a string of
        length 40.  The first 20 bytes will be the SHA-1 of the first 512 bytes
        of the file, and the last 20 bytes will be the SHA-1 of the next 512
        bytes.
        
        @param hash_algorithm: the name of the hash algorithm to use (normally
            C{"sha1"} or C{"md5"})
        @type hash_algorithm: str
        @param offset: offset into the file to begin hashing (0 means to start
            from the beginning)
        @type offset: int or long
        @param length: number of bytes to hash (0 means continue to the end of
            the file)
        @type length: int or long
        @param block_size: number of bytes to hash per result (must not be less
            than 256; 0 means to compute only one hash of the entire segment)
        @type block_size: int
        @return: string of bytes representing the hash of each block,
            concatenated together
        @rtype: str
        
        @note: Many (most?) servers don't support this extension yet.
        
        @raise IOError: if the server doesn't support the "check-file"
            extension, or possibly doesn't support the hash algorithm
            requested
            
        @since: 1.4
        """
        t, msg = self.sftp._request(CMD_EXTENDED, 'check-file', self.handle,
                                    hash_algorithm, long(offset), long(length), block_size)
        ext = msg.get_string()
        alg = msg.get_string()
        data = msg.get_remainder()
        return data
    
    def set_pipelined(self, pipelined=True):
        """
        Turn on/off the pipelining of write operations to this file.  When
        pipelining is on, paramiko won't wait for the server response after
        each write operation.  Instead, they're collected as they come in.
        At the first non-write operation (including L{close}), all remaining
        server responses are collected.  This means that if there was an error
        with one of your later writes, an exception might be thrown from
        within L{close} instead of L{write}.
        
        By default, files are I{not} pipelined.
        
        @param pipelined: C{True} if pipelining should be turned on for this
            file; C{False} otherwise
        @type pipelined: bool
        
        @since: 1.5
        """
        self.pipelined = pipelined
    
    def prefetch(self):
        """
        Pre-fetch the remaining contents of this file in anticipation of
        future L{read} calls.  If reading the entire file, pre-fetching can
        dramatically improve the download speed by avoiding roundtrip latency.
        The file's contents are incrementally buffered in a background thread.
        
        The prefetched data is stored in a buffer until read via the L{read}
        method.  Once data has been read, it's removed from the buffer.  The
        data may be read in a random order (using L{seek}); chunks of the
        buffer that haven't been read will continue to be buffered.

        @since: 1.5.1
        """
        size = self.stat().st_size
        # queue up async reads for the rest of the file
        chunks = []
        n = self._realpos
        while n < size:
            chunk = min(self.MAX_REQUEST_SIZE, size - n)
            chunks.append((n, chunk))
            n += chunk
        if len(chunks) > 0:
            self._start_prefetch(chunks)
    
    def readv(self, chunks):
        """
        Read a set of blocks from the file by (offset, length).  This is more
        efficient than doing a series of L{seek} and L{read} calls, since the
        prefetch machinery is used to retrieve all the requested blocks at
        once.
        
        @param chunks: a list of (offset, length) tuples indicating which
            sections of the file to read
        @type chunks: list(tuple(long, int))
        @return: a list of blocks read, in the same order as in C{chunks}
        @rtype: list(str)
        
        @since: 1.5.4
        """
        self.sftp._log(DEBUG, 'readv(%s, %r)' % (hexlify(self.handle), chunks))

        read_chunks = []
        for offset, size in chunks:
            # don't fetch data that's already in the prefetch buffer
            if self._data_in_prefetch_buffers(offset) or self._data_in_prefetch_requests(offset, size):
                continue

            # break up anything larger than the max read size
            while size > 0:
                chunk_size = min(size, self.MAX_REQUEST_SIZE)
                read_chunks.append((offset, chunk_size))
                offset += chunk_size
                size -= chunk_size

        self._start_prefetch(read_chunks)
        # now we can just devolve to a bunch of read()s :)
        for x in chunks:
            self.seek(x[0])
            yield self.read(x[1])
    

    ###  internals...


    def _get_size(self):
        try:
            return self.stat().st_size
        except:
            return 0

    def _start_prefetch(self, chunks):
        self._prefetching = True
        self._prefetch_done = False
        self._prefetch_reads.extend(chunks)

        t = threading.Thread(target=self._prefetch_thread, args=(chunks,))
        t.setDaemon(True)
        t.start()
        
    def _prefetch_thread(self, chunks):
        # do these read requests in a temporary thread because there may be
        # a lot of them, so it may block.
        for offset, length in chunks:
            self.sftp._async_request(self, CMD_READ, self.handle, long(offset), int(length))

    def _async_response(self, t, msg):
        if t == CMD_STATUS:
            # save exception and re-raise it on next file operation
            try:
                self.sftp._convert_status(msg)
            except Exception, x:
                self._saved_exception = x
            return
        if t != CMD_DATA:
            raise SFTPError('Expected data')
        data = msg.get_string()
        offset, length = self._prefetch_reads.pop(0)
        self._prefetch_data[offset] = data
        if len(self._prefetch_reads) == 0:
            self._prefetch_done = True
    
    def _check_exception(self):
        "if there's a saved exception, raise & clear it"
        if self._saved_exception is not None:
            x = self._saved_exception
            self._saved_exception = None
            raise x
