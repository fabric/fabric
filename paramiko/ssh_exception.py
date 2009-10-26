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
Exceptions defined by paramiko.
"""


class SSHException (Exception):
    """
    Exception raised by failures in SSH2 protocol negotiation or logic errors.
    """
    pass


class AuthenticationException (SSHException):
    """
    Exception raised when authentication failed for some reason.  It may be
    possible to retry with different credentials.  (Other classes specify more
    specific reasons.)
    
    @since: 1.6
    """
    pass
    

class PasswordRequiredException (AuthenticationException):
    """
    Exception raised when a password is needed to unlock a private key file.
    """
    pass


class BadAuthenticationType (AuthenticationException):
    """
    Exception raised when an authentication type (like password) is used, but
    the server isn't allowing that type.  (It may only allow public-key, for
    example.)
    
    @ivar allowed_types: list of allowed authentication types provided by the
        server (possible values are: C{"none"}, C{"password"}, and
        C{"publickey"}).
    @type allowed_types: list
    
    @since: 1.1
    """
    allowed_types = []
    
    def __init__(self, explanation, types):
        AuthenticationException.__init__(self, explanation)
        self.allowed_types = types
     
    def __str__(self):
        return SSHException.__str__(self) + ' (allowed_types=%r)' % self.allowed_types


class PartialAuthentication (AuthenticationException):
    """
    An internal exception thrown in the case of partial authentication.
    """
    allowed_types = []
    
    def __init__(self, types):
        AuthenticationException.__init__(self, 'partial authentication')
        self.allowed_types = types


class ChannelException (SSHException):
    """
    Exception raised when an attempt to open a new L{Channel} fails.
    
    @ivar code: the error code returned by the server
    @type code: int
    
    @since: 1.6
    """
    def __init__(self, code, text):
        SSHException.__init__(self, text)
        self.code = code


class BadHostKeyException (SSHException):
    """
    The host key given by the SSH server did not match what we were expecting.
    
    @ivar hostname: the hostname of the SSH server
    @type hostname: str
    @ivar key: the host key presented by the server
    @type key: L{PKey}
    @ivar expected_key: the host key expected
    @type expected_key: L{PKey}
    
    @since: 1.6
    """
    def __init__(self, hostname, got_key, expected_key):
        SSHException.__init__(self, 'Host key for server %s does not match!' % hostname)
        self.hostname = hostname
        self.key = got_key
        self.expected_key = expected_key

