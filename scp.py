
# scp.py - scp extension for paramiko.
# Copyright (C) 2008 James Bardin <jbardin@bu.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""
Utilities for sending files over ssh using the scp1 protocol.
"""

import os
from socket import timeout as SocketTimeout

class SCPClient(object):
    """
    An scp1 implementation, compatible with openssh scp. SCPClient opens a
    simple scp session with the server, and only copies files.
    """
    def __init__(self, transport, base_path='.',
                 recursive=False, preserve_times=False, 
                 buff_size=16384, socket_timeout=5.0):
        """
        Create an scp1 client.

        @param transport: an existing L{Transport}
        @type transport: L{Transport}
        @param base_path: the destination path
        @type base_path: str
        @param recursive: open a recursive session (scp -r)
        @type recursive: bool
        @param preserve_times: preserve mtime and atime when copying.
        @type preserve_times: bool
        @param buff_size: size of the scp send buffer.
        @type buff_size: int
        """
        self.transport = transport
        self.base_path = base_path
        self.recursive = recursive
        self.preserve_times = preserve_times
        self.buff_size = buff_size
        self.socket_timeout = socket_timeout
        self.showprogress = False
        self.prog = self.Progress()
        self.channel = self.transport.open_session()
        self.channel.settimeout(self.socket_timeout)
        # start the session on the server
        scp_command = ('scp -t %s\n', 'scp -rt %s\n')[self.recursive]
        self.channel.exec_command(scp_command % self.base_path)
        self._confirm()

    def send_file(self, name, remote_name=''):
        """
        Send a file using scp1

        @param name: name of the local file to be copied
        @type name: str
        @param remote_name: name for the remote copy of the file,
            if different from name.
        @type remote_name: str
        """
        remote_name = remote_name or name
        (mode, size, mtime, atime) = self._get_stats(name)
        if self.preserve_times:
            self._send_time(mtime, atime)
        file_hdl = file(name, 'rb')
        self.channel.sendall('C%s %d %s\n' % (mode, size, remote_name))
        self._confirm()
        file_pos = 0
        buff_size = self.buff_size
        while file_pos < size:
            self.channel.sendall(file_hdl.read(buff_size))
            file_pos = file_hdl.tell()
            self.prog.current = (file_pos, size)
        self._end()
        self.prog.current = (0, 0)
        
    def push_dir(self, dir_name, remote_name=''):
        """
        Create remote directory dir_name if it doesn't exist, and move into
        said sirectory.

        @param dir_name: directory name to be pushed to scp server
        @type dir_name: str
        """
        if not self.recursive:
            raise SCPException('Must be in recursive mode to push directories')
        remote_name = remote_name or dir_name
        (mode, size, mtime, atime) = self._get_stats(dir_name)
        if self.preserve_times:
            self._send_time(mtime, atime)
        self.channel.sendall('D%s 0 %s\n' % (mode, remote_name))
        self._confirm()

    def pop_dir(self):
        """
        Move up one level in the remote directory stack. You cannot pop more
        directories than you have previously pushed.
        """
        if not self.recursive:
            raise SCPException('Must be in recursive mode to pop directories')
        self.channel.sendall('E\n')
        self._confirm()
    
    def close(self):
        """
        Close the underlying channel.
        """
        self.channel.close()

    def _get_stats(self, name):
        """return just the file stats needed for scp"""
        stats = os.stat(name)
        mode = oct(stats.st_mode)[-4:]
        size = stats.st_size
        atime = int(stats.st_atime)
        mtime = int(stats.st_mtime)
        return (mode, size, mtime, atime)

    def _send_time(self, mtime, atime):
        """send atime and mtime of the file"""
        self.channel.sendall('T%d 0 %d 0\n' % (mtime, atime))
        self._confirm()

    def _confirm(self):
        """read scp response"""
        try:
            msg = self.channel.recv(512)
        except SocketTimeout:
            raise SCPException('Timout waiting for scp response')
        if not msg == '\x00':
            raise SCPException(msg)
    
    def _end(self):
        """confirm EOF"""
        self.channel.sendall('\x00')
        self._confirm()

    def get_progress(self):
        """
        Return an object with only one attribute called "current".
        "current" is a tuple containing current file position, and file size,
        which is updated during file transfers.
        """
        self.showprogress = True
        return self.prog

    class Progress(object):
        def __init__(self):
            self.current = (0, 0)


class SCPException(Exception):
    """SCP exception class"""
    pass
