#!/usr/bin/python
# -*- coding: ascii -*-
# Copyright (C) 2008  Dwayne C. Litzenberger <dlitz@dlitz.net>
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

import sys
import threading
from Crypto.Util.randpool import RandomPool as _RandomPool

try:
    import platform
except ImportError:
    platform = None     # Not available using Python 2.2

def _strxor(a, b):
    assert len(a) == len(b)
    return "".join(map(lambda x, y: chr(ord(x) ^ ord(y)), a, b))

##
## Find a strong random entropy source, depending on the detected platform.
## WARNING TO DEVELOPERS: This will fail on some systems, but do NOT use
## Crypto.Util.randpool.RandomPool as a fall-back.  RandomPool will happily run
## with very little entropy, thus _silently_ defeating any security that
## Paramiko attempts to provide.  (This is current as of PyCrypto 2.0.1).
## See http://www.lag.net/pipermail/paramiko/2008-January/000599.html
## and http://www.lag.net/pipermail/paramiko/2008-April/000678.html
##

if ((platform is not None and platform.system().lower() == 'windows') or
        sys.platform == 'win32'):
    # MS Windows
    from paramiko import rng_win32
    rng_device = rng_win32.open_rng_device()
else:
    # Assume POSIX (any system where /dev/urandom exists)
    from paramiko import rng_posix
    rng_device = rng_posix.open_rng_device()


class StrongLockingRandomPool(object):
    """Wrapper around RandomPool guaranteeing strong random numbers.
    
    Crypto.Util.randpool.RandomPool will silently operate even if it is seeded
    with little or no entropy, and it provides no prediction resistance if its
    state is ever compromised throughout its runtime.  It is also not thread-safe.

    This wrapper augments RandomPool by XORing its output with random bits from
    the operating system, and by controlling access to the underlying
    RandomPool using an exclusive lock.
    """

    def __init__(self, instance=None):
        if instance is None:
            instance = _RandomPool()
        self.randpool = instance
        self.randpool_lock = threading.Lock()
        self.entropy = rng_device

        # Stir 256 bits of entropy from the RNG device into the RandomPool.
        self.randpool.stir(self.entropy.read(32))
        self.entropy.randomize()

    def stir(self, s=''):
        self.randpool_lock.acquire()
        try:
            self.randpool.stir(s)
        finally:
            self.randpool_lock.release()
        self.entropy.randomize()

    def randomize(self, N=0):
        self.randpool_lock.acquire()
        try:
            self.randpool.randomize(N)
        finally:
            self.randpool_lock.release()
        self.entropy.randomize()

    def add_event(self, s=''):
        self.randpool_lock.acquire()
        try:
            self.randpool.add_event(s)
        finally:
            self.randpool_lock.release()

    def get_bytes(self, N):
        self.randpool_lock.acquire()
        try:
            randpool_data = self.randpool.get_bytes(N)
        finally:
            self.randpool_lock.release()
        entropy_data = self.entropy.read(N)
        result = _strxor(randpool_data, entropy_data)
        assert len(randpool_data) == N and len(entropy_data) == N and len(result) == N
        return result

# vim:set ts=4 sw=4 sts=4 expandtab:
