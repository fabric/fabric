# Copyright (C) 2003-2007  John Rochester <john@jrochester.org>
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
SSH Agent interface for Unix clients.
"""

import os
import socket
import struct
import sys

from paramiko.ssh_exception import SSHException
from paramiko.message import Message
from paramiko.pkey import PKey


SSH2_AGENTC_REQUEST_IDENTITIES, SSH2_AGENT_IDENTITIES_ANSWER, \
    SSH2_AGENTC_SIGN_REQUEST, SSH2_AGENT_SIGN_RESPONSE = range(11, 15)


class Agent:
    """
    Client interface for using private keys from an SSH agent running on the
    local machine.  If an SSH agent is running, this class can be used to
    connect to it and retreive L{PKey} objects which can be used when
    attempting to authenticate to remote SSH servers.
    
    Because the SSH agent protocol uses environment variables and unix-domain
    sockets, this probably doesn't work on Windows.  It does work on most
    posix platforms though (Linux and MacOS X, for example).
    """
    
    def __init__(self):
        """
        Open a session with the local machine's SSH agent, if one is running.
        If no agent is running, initialization will succeed, but L{get_keys}
        will return an empty tuple.
        
        @raise SSHException: if an SSH agent is found, but speaks an
            incompatible protocol
        """
        self.keys = ()
        if ('SSH_AUTH_SOCK' in os.environ) and (sys.platform != 'win32'):
            conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                conn.connect(os.environ['SSH_AUTH_SOCK'])
            except:
                # probably a dangling env var: the ssh agent is gone
                return
            self.conn = conn
        elif sys.platform == 'win32':
            import win_pageant
            if win_pageant.can_talk_to_agent():
                self.conn = win_pageant.PageantConnection()
            else:
                return
        else:
            # no agent support
            return
            
        ptype, result = self._send_message(chr(SSH2_AGENTC_REQUEST_IDENTITIES))
        if ptype != SSH2_AGENT_IDENTITIES_ANSWER:
            raise SSHException('could not get keys from ssh-agent')
        keys = []
        for i in range(result.get_int()):
            keys.append(AgentKey(self, result.get_string()))
            result.get_string()
        self.keys = tuple(keys)

    def close(self):
        """
        Close the SSH agent connection.
        """
        self.conn.close()
        self.conn = None
        self.keys = ()

    def get_keys(self):
        """
        Return the list of keys available through the SSH agent, if any.  If
        no SSH agent was running (or it couldn't be contacted), an empty list
        will be returned.
        
        @return: a list of keys available on the SSH agent
        @rtype: tuple of L{AgentKey}
        """
        return self.keys

    def _send_message(self, msg):
        msg = str(msg)
        self.conn.send(struct.pack('>I', len(msg)) + msg)
        l = self._read_all(4)
        msg = Message(self._read_all(struct.unpack('>I', l)[0]))
        return ord(msg.get_byte()), msg

    def _read_all(self, wanted):
        result = self.conn.recv(wanted)
        while len(result) < wanted:
            if len(result) == 0:
                raise SSHException('lost ssh-agent')
            extra = self.conn.recv(wanted - len(result))
            if len(extra) == 0:
                raise SSHException('lost ssh-agent')
            result += extra
        return result


class AgentKey(PKey):
    """
    Private key held in a local SSH agent.  This type of key can be used for
    authenticating to a remote server (signing).  Most other key operations
    work as expected.
    """
    
    def __init__(self, agent, blob):
        self.agent = agent
        self.blob = blob
        self.name = Message(blob).get_string()

    def __str__(self):
        return self.blob

    def get_name(self):
        return self.name

    def sign_ssh_data(self, randpool, data):
        msg = Message()
        msg.add_byte(chr(SSH2_AGENTC_SIGN_REQUEST))
        msg.add_string(self.blob)
        msg.add_string(data)
        msg.add_int(0)
        ptype, result = self.agent._send_message(msg)
        if ptype != SSH2_AGENT_SIGN_RESPONSE:
            raise SSHException('key cannot be used for signing')
        return result.get_string()
