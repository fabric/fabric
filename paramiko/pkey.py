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
Common API for all public keys.
"""

import base64
from binascii import hexlify, unhexlify
import os

from Crypto.Hash import MD5
from Crypto.Cipher import DES3

from paramiko.common import *
from paramiko import util
from paramiko.message import Message
from paramiko.ssh_exception import SSHException, PasswordRequiredException


class PKey (object):
    """
    Base class for public keys.
    """

    # known encryption types for private key files:
    _CIPHER_TABLE = {
        'DES-EDE3-CBC': { 'cipher': DES3, 'keysize': 24, 'blocksize': 8, 'mode': DES3.MODE_CBC }
    }


    def __init__(self, msg=None, data=None):
        """
        Create a new instance of this public key type.  If C{msg} is given,
        the key's public part(s) will be filled in from the message.  If
        C{data} is given, the key's public part(s) will be filled in from
        the string.

        @param msg: an optional SSH L{Message} containing a public key of this
        type.
        @type msg: L{Message}
        @param data: an optional string containing a public key of this type
        @type data: str

        @raise SSHException: if a key cannot be created from the C{data} or
        C{msg} given, or no key was passed in.
        """
        pass

    def __str__(self):
        """
        Return a string of an SSH L{Message} made up of the public part(s) of
        this key.  This string is suitable for passing to L{__init__} to
        re-create the key object later.

        @return: string representation of an SSH key message.
        @rtype: str
        """
        return ''

    def __cmp__(self, other):
        """
        Compare this key to another.  Returns 0 if this key is equivalent to
        the given key, or non-0 if they are different.  Only the public parts
        of the key are compared, so a public key will compare equal to its
        corresponding private key.

        @param other: key to compare to.
        @type other: L{PKey}
        @return: 0 if the two keys are equivalent, non-0 otherwise.
        @rtype: int
        """
        hs = hash(self)
        ho = hash(other)
        if hs != ho:
            return cmp(hs, ho)
        return cmp(str(self), str(other))

    def get_name(self):
        """
        Return the name of this private key implementation.

        @return: name of this private key type, in SSH terminology (for
        example, C{"ssh-rsa"}).
        @rtype: str
        """
        return ''

    def get_bits(self):
        """
        Return the number of significant bits in this key.  This is useful
        for judging the relative security of a key.

        @return: bits in the key.
        @rtype: int
        """
        return 0

    def can_sign(self):
        """
        Return C{True} if this key has the private part necessary for signing
        data.

        @return: C{True} if this is a private key.
        @rtype: bool
        """
        return False

    def get_fingerprint(self):
        """
        Return an MD5 fingerprint of the public part of this key.  Nothing
        secret is revealed.

        @return: a 16-byte string (binary) of the MD5 fingerprint, in SSH
            format.
        @rtype: str
        """
        return MD5.new(str(self)).digest()

    def get_base64(self):
        """
        Return a base64 string containing the public part of this key.  Nothing
        secret is revealed.  This format is compatible with that used to store
        public key files or recognized host keys.

        @return: a base64 string containing the public part of the key.
        @rtype: str
        """
        return base64.encodestring(str(self)).replace('\n', '')

    def sign_ssh_data(self, randpool, data):
        """
        Sign a blob of data with this private key, and return a L{Message}
        representing an SSH signature message.

        @param randpool: a secure random number generator.
        @type randpool: L{Crypto.Util.randpool.RandomPool}
        @param data: the data to sign.
        @type data: str
        @return: an SSH signature message.
        @rtype: L{Message}
        """
        return ''

    def verify_ssh_sig(self, data, msg):
        """
        Given a blob of data, and an SSH message representing a signature of
        that data, verify that it was signed with this key.

        @param data: the data that was signed.
        @type data: str
        @param msg: an SSH signature message
        @type msg: L{Message}
        @return: C{True} if the signature verifies correctly; C{False}
            otherwise.
        @rtype: boolean
        """
        return False
   
    def from_private_key_file(cls, filename, password=None):
        """
        Create a key object by reading a private key file.  If the private
        key is encrypted and C{password} is not C{None}, the given password
        will be used to decrypt the key (otherwise L{PasswordRequiredException}
        is thrown).  Through the magic of python, this factory method will
        exist in all subclasses of PKey (such as L{RSAKey} or L{DSSKey}), but
        is useless on the abstract PKey class.

        @param filename: name of the file to read
        @type filename: str
        @param password: an optional password to use to decrypt the key file,
            if it's encrypted
        @type password: str
        @return: a new key object based on the given private key
        @rtype: L{PKey}

        @raise IOError: if there was an error reading the file
        @raise PasswordRequiredException: if the private key file is
            encrypted, and C{password} is C{None}
        @raise SSHException: if the key file is invalid
        """
        key = cls(filename=filename, password=password)
        return key
    from_private_key_file = classmethod(from_private_key_file)

    def from_private_key(cls, file_obj, password=None):
        """
        Create a key object by reading a private key from a file (or file-like)
        object.  If the private key is encrypted and C{password} is not C{None},
        the given password will be used to decrypt the key (otherwise
        L{PasswordRequiredException} is thrown).
        
        @param file_obj: the file to read from
        @type file_obj: file
        @param password: an optional password to use to decrypt the key, if it's
            encrypted
        @type password: str
        @return: a new key object based on the given private key
        @rtype: L{PKey}
        
        @raise IOError: if there was an error reading the key
        @raise PasswordRequiredException: if the private key file is encrypted,
            and C{password} is C{None}
        @raise SSHException: if the key file is invalid
        """
        key = cls(file_obj=file_obj, password=password)
        return key
    from_private_key = classmethod(from_private_key)

    def write_private_key_file(self, filename, password=None):
        """
        Write private key contents into a file.  If the password is not
        C{None}, the key is encrypted before writing.

        @param filename: name of the file to write
        @type filename: str
        @param password: an optional password to use to encrypt the key file
        @type password: str

        @raise IOError: if there was an error writing the file
        @raise SSHException: if the key is invalid
        """
        raise Exception('Not implemented in PKey')
    
    def write_private_key(self, file_obj, password=None):
        """
        Write private key contents into a file (or file-like) object.  If the
        password is not C{None}, the key is encrypted before writing.
        
        @param file_obj: the file object to write into
        @type file_obj: file
        @param password: an optional password to use to encrypt the key
        @type password: str
        
        @raise IOError: if there was an error writing to the file
        @raise SSHException: if the key is invalid
        """
        raise Exception('Not implemented in PKey')

    def _read_private_key_file(self, tag, filename, password=None):
        """
        Read an SSH2-format private key file, looking for a string of the type
        C{"BEGIN xxx PRIVATE KEY"} for some C{xxx}, base64-decode the text we
        find, and return it as a string.  If the private key is encrypted and
        C{password} is not C{None}, the given password will be used to decrypt
        the key (otherwise L{PasswordRequiredException} is thrown).

        @param tag: C{"RSA"} or C{"DSA"}, the tag used to mark the data block.
        @type tag: str
        @param filename: name of the file to read.
        @type filename: str
        @param password: an optional password to use to decrypt the key file,
            if it's encrypted.
        @type password: str
        @return: data blob that makes up the private key.
        @rtype: str

        @raise IOError: if there was an error reading the file.
        @raise PasswordRequiredException: if the private key file is
            encrypted, and C{password} is C{None}.
        @raise SSHException: if the key file is invalid.
        """
        f = open(filename, 'r')
        data = self._read_private_key(tag, f, password)
        f.close()
        return data
    
    def _read_private_key(self, tag, f, password=None):
        lines = f.readlines()
        start = 0
        while (start < len(lines)) and (lines[start].strip() != '-----BEGIN ' + tag + ' PRIVATE KEY-----'):
            start += 1
        if start >= len(lines):
            raise SSHException('not a valid ' + tag + ' private key file')
        # parse any headers first
        headers = {}
        start += 1
        while start < len(lines):
            l = lines[start].split(': ')
            if len(l) == 1:
                break
            headers[l[0].lower()] = l[1].strip()
            start += 1
        # find end
        end = start
        while (lines[end].strip() != '-----END ' + tag + ' PRIVATE KEY-----') and (end < len(lines)):
            end += 1
        # if we trudged to the end of the file, just try to cope.
        try:
            data = base64.decodestring(''.join(lines[start:end]))
        except base64.binascii.Error, e:
            raise SSHException('base64 decoding error: ' + str(e))
        if 'proc-type' not in headers:
            # unencryped: done
            return data
        # encrypted keyfile: will need a password
        if headers['proc-type'] != '4,ENCRYPTED':
            raise SSHException('Unknown private key structure "%s"' % headers['proc-type'])
        try:
            encryption_type, saltstr = headers['dek-info'].split(',')
        except:
            raise SSHException('Can\'t parse DEK-info in private key file')
        if encryption_type not in self._CIPHER_TABLE:
            raise SSHException('Unknown private key cipher "%s"' % encryption_type)
        # if no password was passed in, raise an exception pointing out that we need one
        if password is None:
            raise PasswordRequiredException('Private key file is encrypted')
        cipher = self._CIPHER_TABLE[encryption_type]['cipher']
        keysize = self._CIPHER_TABLE[encryption_type]['keysize']
        mode = self._CIPHER_TABLE[encryption_type]['mode']
        salt = unhexlify(saltstr)
        key = util.generate_key_bytes(MD5, salt, password, keysize)
        return cipher.new(key, mode, salt).decrypt(data)

    def _write_private_key_file(self, tag, filename, data, password=None):
        """
        Write an SSH2-format private key file in a form that can be read by
        paramiko or openssh.  If no password is given, the key is written in
        a trivially-encoded format (base64) which is completely insecure.  If
        a password is given, DES-EDE3-CBC is used.

        @param tag: C{"RSA"} or C{"DSA"}, the tag used to mark the data block.
        @type tag: str
        @param filename: name of the file to write.
        @type filename: str
        @param data: data blob that makes up the private key.
        @type data: str
        @param password: an optional password to use to encrypt the file.
        @type password: str

        @raise IOError: if there was an error writing the file.
        """
        f = open(filename, 'w', 0600)
        # grrr... the mode doesn't always take hold
        os.chmod(filename, 0600)
        self._write_private_key(tag, f, data, password)
        f.close()
    
    def _write_private_key(self, tag, f, data, password=None):
        f.write('-----BEGIN %s PRIVATE KEY-----\n' % tag)
        if password is not None:
            # since we only support one cipher here, use it
            cipher_name = self._CIPHER_TABLE.keys()[0]
            cipher = self._CIPHER_TABLE[cipher_name]['cipher']
            keysize = self._CIPHER_TABLE[cipher_name]['keysize']
            blocksize = self._CIPHER_TABLE[cipher_name]['blocksize']
            mode = self._CIPHER_TABLE[cipher_name]['mode']
            salt = randpool.get_bytes(8)
            key = util.generate_key_bytes(MD5, salt, password, keysize)
            if len(data) % blocksize != 0:
                n = blocksize - len(data) % blocksize
                #data += randpool.get_bytes(n)
                # that would make more sense ^, but it confuses openssh.
                data += '\0' * n
            data = cipher.new(key, mode, salt).encrypt(data)
            f.write('Proc-Type: 4,ENCRYPTED\n')
            f.write('DEK-Info: %s,%s\n' % (cipher_name, hexlify(salt).upper()))
            f.write('\n')
        s = base64.encodestring(data)
        # re-wrap to 64-char lines
        s = ''.join(s.split('\n'))
        s = '\n'.join([s[i : i+64] for i in range(0, len(s), 64)])
        f.write(s)
        f.write('\n')
        f.write('-----END %s PRIVATE KEY-----\n' % tag)
