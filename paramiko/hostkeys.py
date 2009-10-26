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
L{HostKeys}
"""

import base64
from Crypto.Hash import SHA, HMAC
import UserDict

from paramiko.common import *
from paramiko.dsskey import DSSKey
from paramiko.rsakey import RSAKey


class HostKeyEntry:
    """
    Representation of a line in an OpenSSH-style "known hosts" file.
    """
    
    def __init__(self, hostnames=None, key=None):
        self.valid = (hostnames is not None) and (key is not None)
        self.hostnames = hostnames
        self.key = key

    def from_line(cls, line):
        """
        Parses the given line of text to find the names for the host,
        the type of key, and the key data. The line is expected to be in the
        format used by the openssh known_hosts file.

        Lines are expected to not have leading or trailing whitespace.
        We don't bother to check for comments or empty lines.  All of
        that should be taken care of before sending the line to us.

        @param line: a line from an OpenSSH known_hosts file
        @type line: str
        """
        fields = line.split(' ')
        if len(fields) != 3:
            # Bad number of fields
            return None

        names, keytype, key = fields
        names = names.split(',')

        # Decide what kind of key we're looking at and create an object
        # to hold it accordingly.
        if keytype == 'ssh-rsa':
            key = RSAKey(data=base64.decodestring(key))
        elif keytype == 'ssh-dss':
            key = DSSKey(data=base64.decodestring(key))
        else:
            return None

        return cls(names, key)
    from_line = classmethod(from_line)

    def to_line(self):
        """
        Returns a string in OpenSSH known_hosts file format, or None if
        the object is not in a valid state.  A trailing newline is
        included.
        """
        if self.valid:
            return '%s %s %s\n' % (','.join(self.hostnames), self.key.get_name(),
                   self.key.get_base64())
        return None
    
    def __repr__(self):
        return '<HostKeyEntry %r: %r>' % (self.hostnames, self.key)


class HostKeys (UserDict.DictMixin):
    """
    Representation of an openssh-style "known hosts" file.  Host keys can be
    read from one or more files, and then individual hosts can be looked up to
    verify server keys during SSH negotiation.
    
    A HostKeys object can be treated like a dict; any dict lookup is equivalent
    to calling L{lookup}.
    
    @since: 1.5.3
    """
    
    def __init__(self, filename=None):
        """
        Create a new HostKeys object, optionally loading keys from an openssh
        style host-key file.
        
        @param filename: filename to load host keys from, or C{None}
        @type filename: str
        """
        # emulate a dict of { hostname: { keytype: PKey } }
        self._entries = []
        if filename is not None:
            self.load(filename)
    
    def add(self, hostname, keytype, key):
        """
        Add a host key entry to the table.  Any existing entry for a
        C{(hostname, keytype)} pair will be replaced.
        
        @param hostname: the hostname (or IP) to add
        @type hostname: str
        @param keytype: key type (C{"ssh-rsa"} or C{"ssh-dss"})
        @type keytype: str
        @param key: the key to add
        @type key: L{PKey}
        """
        for e in self._entries:
            if (hostname in e.hostnames) and (e.key.get_name() == keytype):
                e.key = key
                return
        self._entries.append(HostKeyEntry([hostname], key))
            
    def load(self, filename):
        """
        Read a file of known SSH host keys, in the format used by openssh.
        This type of file unfortunately doesn't exist on Windows, but on
        posix, it will usually be stored in
        C{os.path.expanduser("~/.ssh/known_hosts")}.
        
        If this method is called multiple times, the host keys are merged,
        not cleared.  So multiple calls to C{load} will just call L{add},
        replacing any existing entries and adding new ones.
        
        @param filename: name of the file to read host keys from
        @type filename: str
        
        @raise IOError: if there was an error reading the file
        """
        f = open(filename, 'r')
        for line in f:
            line = line.strip()
            if (len(line) == 0) or (line[0] == '#'):
                continue
            e = HostKeyEntry.from_line(line)
            if e is not None:
                self._entries.append(e)
        f.close()
    
    def save(self, filename):
        """
        Save host keys into a file, in the format used by openssh.  The order of
        keys in the file will be preserved when possible (if these keys were
        loaded from a file originally).  The single exception is that combined
        lines will be split into individual key lines, which is arguably a bug.
        
        @param filename: name of the file to write
        @type filename: str
        
        @raise IOError: if there was an error writing the file
        
        @since: 1.6.1
        """
        f = open(filename, 'w')
        for e in self._entries:
            line = e.to_line()
            if line:
                f.write(line)
        f.close()

    def lookup(self, hostname):
        """
        Find a hostkey entry for a given hostname or IP.  If no entry is found,
        C{None} is returned.  Otherwise a dictionary of keytype to key is
        returned.  The keytype will be either C{"ssh-rsa"} or C{"ssh-dss"}.
        
        @param hostname: the hostname (or IP) to lookup
        @type hostname: str
        @return: keys associated with this host (or C{None})
        @rtype: dict(str, L{PKey})
        """
        class SubDict (UserDict.DictMixin):
            def __init__(self, hostname, entries, hostkeys):
                self._hostname = hostname
                self._entries = entries
                self._hostkeys = hostkeys
            
            def __getitem__(self, key):
                for e in self._entries:
                    if e.key.get_name() == key:
                        return e.key
                raise KeyError(key)
            
            def __setitem__(self, key, val):
                for e in self._entries:
                    if e.key is None:
                        continue
                    if e.key.get_name() == key:
                        # replace
                        e.key = val
                        break
                else:
                    # add a new one
                    e = HostKeyEntry([hostname], val)
                    self._entries.append(e)
                    self._hostkeys._entries.append(e)
            
            def keys(self):
                return [e.key.get_name() for e in self._entries if e.key is not None]

        entries = []
        for e in self._entries:
            for h in e.hostnames:
                if (h.startswith('|1|') and (self.hash_host(hostname, h) == h)) or (h == hostname):
                    entries.append(e)
        if len(entries) == 0:
            return None
        return SubDict(hostname, entries, self)
    
    def check(self, hostname, key):
        """
        Return True if the given key is associated with the given hostname
        in this dictionary.
        
        @param hostname: hostname (or IP) of the SSH server
        @type hostname: str
        @param key: the key to check
        @type key: L{PKey}
        @return: C{True} if the key is associated with the hostname; C{False}
            if not
        @rtype: bool
        """
        k = self.lookup(hostname)
        if k is None:
            return False
        host_key = k.get(key.get_name(), None)
        if host_key is None:
            return False
        return str(host_key) == str(key)

    def clear(self):
        """
        Remove all host keys from the dictionary.
        """
        self._entries = []
    
    def __getitem__(self, key):
        ret = self.lookup(key)
        if ret is None:
            raise KeyError(key)
        return ret
    
    def __setitem__(self, hostname, entry):
        # don't use this please.
        if len(entry) == 0:
            self._entries.append(HostKeyEntry([hostname], None))
            return
        for key_type in entry.keys():
            found = False
            for e in self._entries:
                if (hostname in e.hostnames) and (e.key.get_name() == key_type):
                    # replace
                    e.key = entry[key_type]
                    found = True
            if not found:
                self._entries.append(HostKeyEntry([hostname], entry[key_type]))
    
    def keys(self):
        # python 2.4 sets would be nice here.
        ret = []
        for e in self._entries:
            for h in e.hostnames:
                if h not in ret:
                    ret.append(h)
        return ret

    def values(self):
        ret = []
        for k in self.keys():
            ret.append(self.lookup(k))
        return ret

    def hash_host(hostname, salt=None):
        """
        Return a "hashed" form of the hostname, as used by openssh when storing
        hashed hostnames in the known_hosts file.
        
        @param hostname: the hostname to hash
        @type hostname: str
        @param salt: optional salt to use when hashing (must be 20 bytes long)
        @type salt: str
        @return: the hashed hostname
        @rtype: str
        """
        if salt is None:
            salt = randpool.get_bytes(SHA.digest_size)
        else:
            if salt.startswith('|1|'):
                salt = salt.split('|')[2]
            salt = base64.decodestring(salt)
        assert len(salt) == SHA.digest_size
        hmac = HMAC.HMAC(salt, hostname, SHA).digest()
        hostkey = '|1|%s|%s' % (base64.encodestring(salt), base64.encodestring(hmac))
        return hostkey.replace('\n', '')
    hash_host = staticmethod(hash_host)

