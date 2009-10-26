# Copyright (C) 2006-2007  Robey Pointer <robey@lag.net>
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
Attempt to generalize the "feeder" part of a Channel: an object which can be
read from and closed, but is reading from a buffer fed by another thread.  The
read operations are blocking and can have a timeout set.
"""

import array
import threading
import time


class PipeTimeout (IOError):
    """
    Indicates that a timeout was reached on a read from a L{BufferedPipe}.
    """
    pass


class BufferedPipe (object):
    """
    A buffer that obeys normal read (with timeout) & close semantics for a
    file or socket, but is fed data from another thread.  This is used by
    L{Channel}.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._event = None
        self._buffer = array.array('B')
        self._closed = False

    def set_event(self, event):
        """
        Set an event on this buffer.  When data is ready to be read (or the
        buffer has been closed), the event will be set.  When no data is
        ready, the event will be cleared.
        
        @param event: the event to set/clear
        @type event: Event
        """
        self._event = event
        if len(self._buffer) > 0:
            event.set()
        else:
            event.clear()
        
    def feed(self, data):
        """
        Feed new data into this pipe.  This method is assumed to be called
        from a separate thread, so synchronization is done.
        
        @param data: the data to add
        @type data: str
        """
        self._lock.acquire()
        try:
            if self._event is not None:
                self._event.set()
            self._buffer.fromstring(data)
            self._cv.notifyAll()
        finally:
            self._lock.release()

    def read_ready(self):
        """
        Returns true if data is buffered and ready to be read from this
        feeder.  A C{False} result does not mean that the feeder has closed;
        it means you may need to wait before more data arrives.
        
        @return: C{True} if a L{read} call would immediately return at least
            one byte; C{False} otherwise.
        @rtype: bool
        """
        self._lock.acquire()
        try:
            if len(self._buffer) == 0:
                return False
            return True
        finally:
            self._lock.release()

    def read(self, nbytes, timeout=None):
        """
        Read data from the pipe.  The return value is a string representing
        the data received.  The maximum amount of data to be received at once
        is specified by C{nbytes}.  If a string of length zero is returned,
        the pipe has been closed.

        The optional C{timeout} argument can be a nonnegative float expressing
        seconds, or C{None} for no timeout.  If a float is given, a
        C{PipeTimeout} will be raised if the timeout period value has
        elapsed before any data arrives.

        @param nbytes: maximum number of bytes to read
        @type nbytes: int
        @param timeout: maximum seconds to wait (or C{None}, the default, to
            wait forever)
        @type timeout: float
        @return: data
        @rtype: str
        
        @raise PipeTimeout: if a timeout was specified and no data was ready
            before that timeout
        """
        out = ''
        self._lock.acquire()
        try:
            if len(self._buffer) == 0:
                if self._closed:
                    return out
                # should we block?
                if timeout == 0.0:
                    raise PipeTimeout()
                # loop here in case we get woken up but a different thread has
                # grabbed everything in the buffer.
                while (len(self._buffer) == 0) and not self._closed:
                    then = time.time()
                    self._cv.wait(timeout)
                    if timeout is not None:
                        timeout -= time.time() - then
                        if timeout <= 0.0:
                            raise PipeTimeout()

            # something's in the buffer and we have the lock!
            if len(self._buffer) <= nbytes:
                out = self._buffer.tostring()
                del self._buffer[:]
                if (self._event is not None) and not self._closed:
                    self._event.clear()
            else:
                out = self._buffer[:nbytes].tostring()
                del self._buffer[:nbytes]
        finally:
            self._lock.release()

        return out
    
    def empty(self):
        """
        Clear out the buffer and return all data that was in it.
        
        @return: any data that was in the buffer prior to clearing it out
        @rtype: str
        """
        self._lock.acquire()
        try:
            out = self._buffer.tostring()
            del self._buffer[:]
            if (self._event is not None) and not self._closed:
                self._event.clear()
            return out
        finally:
            self._lock.release()
    
    def close(self):
        """
        Close this pipe object.  Future calls to L{read} after the buffer
        has been emptied will return immediately with an empty string.
        """
        self._lock.acquire()
        try:
            self._closed = True
            self._cv.notifyAll()
            if self._event is not None:
                self._event.set()
        finally:
            self._lock.release()

    def __len__(self):
        """
        Return the number of bytes buffered.
        
        @return: number of bytes bufferes
        @rtype: int
        """
        self._lock.acquire()
        try:
            return len(self._buffer)
        finally:
            self._lock.release()

