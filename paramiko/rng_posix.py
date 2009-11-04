#!/usr/bin/python
# -*- coding: ascii -*-
# Copyright (C) 2008  Dwayne C. Litzenberger <dlitz@dlitz.net>
# Copyright (C) 2008  Open Systems Canada Limited
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
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import stat

class error(Exception):
    pass

class _RNG(object):
    def __init__(self, file):
        self.file = file

    def read(self, bytes):
        return self.file.read(bytes)

    def close(self):
        return self.file.close()

    def randomize(self):
        return

def open_rng_device(device_path=None):
    """Open /dev/urandom and perform some sanity checks."""

    f = None
    g = None
    
    if device_path is None:
        device_path = "/dev/urandom"

    try:
        # Try to open /dev/urandom now so that paramiko will be able to access
        # it even if os.chroot() is invoked later.
        try:
            f = open(device_path, "rb", 0)
        except EnvironmentError:
            raise error("Unable to open /dev/urandom")
        
        # Open a second file descriptor for sanity checking later.
        try:
            g = open(device_path, "rb", 0)
        except EnvironmentError:
            raise error("Unable to open /dev/urandom")

        # Check that /dev/urandom is a character special device, not a regular file.
        st = os.fstat(f.fileno())   # f
        if stat.S_ISREG(st.st_mode) or not stat.S_ISCHR(st.st_mode):
            raise error("/dev/urandom is not a character special device")
        
        st = os.fstat(g.fileno())   # g
        if stat.S_ISREG(st.st_mode) or not stat.S_ISCHR(st.st_mode):
            raise error("/dev/urandom is not a character special device")
        
        # Check that /dev/urandom always returns the number of bytes requested
        x = f.read(20)
        y = g.read(20)
        if len(x) != 20 or len(y) != 20:
            raise error("Error reading from /dev/urandom: input truncated")
    
        # Check that different reads return different data
        if x == y:
            raise error("/dev/urandom is broken; returning identical data: %r == %r" % (x, y))

        # Close the duplicate file object
        g.close()

        # Return the first file object
        return _RNG(f)

    except error:
        if f is not None:
            f.close()
        if g is not None:
            g.close()
        raise

# vim:set ts=4 sw=4 sts=4 expandtab:

