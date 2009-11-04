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

class error(Exception):
    pass

# Try to import the "winrandom" module
try:
    from Crypto.Util import winrandom as _winrandom
except ImportError:
    _winrandom = None

# Try to import the "urandom" module
try:
    from os import urandom as _urandom
except ImportError:
    _urandom = None


class _RNG(object):
    def __init__(self, readfunc):
        self.read = readfunc

    def randomize(self):
        # According to "Cryptanalysis of the Random Number Generator of the
        # Windows Operating System", by Leo Dorrendorf and Zvi Gutterman
        # and Benny Pinkas <http://eprint.iacr.org/2007/419>,
        # CryptGenRandom only updates its internal state using kernel-provided
        # random data every 128KiB of output.
        self.read(128*1024)    # discard 128 KiB of output

def _open_winrandom():
    if _winrandom is None:
        raise error("Crypto.Util.winrandom module not found")
    
    # Check that we can open the winrandom module
    try:
        r0 = _winrandom.new()
        r1 = _winrandom.new()
    except Exception, exc:
        raise error("winrandom.new() failed: %s" % str(exc), exc)
    
    # Check that we can read from the winrandom module
    try:
        x = r0.get_bytes(20)
        y = r1.get_bytes(20)
    except Exception, exc:
        raise error("winrandom get_bytes failed: %s" % str(exc), exc)

    # Check that the requested number of bytes are returned
    if len(x) != 20 or len(y) != 20:
        raise error("Error reading from winrandom: input truncated")

    # Check that different reads return different data
    if x == y:
        raise error("winrandom broken: returning identical data")

    return _RNG(r0.get_bytes)

def _open_urandom():
    if _urandom is None:
        raise error("os.urandom function not found")
    
    # Check that we can read from os.urandom()
    try:
        x = _urandom(20)
        y = _urandom(20)
    except Exception, exc:
        raise error("os.urandom failed: %s" % str(exc), exc)

    # Check that the requested number of bytes are returned
    if len(x) != 20 or len(y) != 20:
        raise error("os.urandom failed: input truncated")

    # Check that different reads return different data
    if x == y:
        raise error("os.urandom failed: returning identical data")

    return _RNG(_urandom)

def open_rng_device():
    # Try using the Crypto.Util.winrandom module
    try:
        return _open_winrandom()
    except error:
        pass

    # Several versions of PyCrypto do not contain the winrandom module, but
    # Python >= 2.4 has os.urandom, so try to use that.
    try:
        return _open_urandom()
    except error:
        pass

    # SECURITY NOTE: DO NOT USE Crypto.Util.randpool.RandomPool HERE!
    # If we got to this point, RandomPool will silently run with very little
    # entropy.  (This is current as of PyCrypto 2.0.1).
    # See http://www.lag.net/pipermail/paramiko/2008-January/000599.html
    # and http://www.lag.net/pipermail/paramiko/2008-April/000678.html

    raise error("Unable to find a strong random entropy source.  You cannot run this software securely under the current configuration.")

# vim:set ts=4 sw=4 sts=4 expandtab:
