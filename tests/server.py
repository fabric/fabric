from __future__ import with_statement
import itertools
import logging
import os
import re
import socket
import sys
import threading
import types
from Python26SocketServer import BaseRequestHandler, ThreadingMixIn, TCPServer

import paramiko as ssh

from fabric.operations import _sudo_prefix
from fabric.api import env


logging.basicConfig(
    filename='/tmp/test_server.log',
    level=logging.DEBUG,
    datefmt='%H:%M:%S',
    format='[%(asctime)s] %(levelname)-8s %(message)s'
)


def _equalize(lists, fillval=None):
    """
    Pad all given list items in ``lists`` to be the same length.
    """
    lists = map(list, lists)
    upper = max(len(x) for x in lists)
    for lst in lists:
        diff = upper - len(lst)
        if diff:
            lst.extend([fillval] * diff)
    return lists


class ParamikoServer(ssh.ServerInterface):
    """
    Test-ready server implementing Paramiko's server interface parent class.

    Mostly just handles the bare minimum necessary to handle SSH-level things
    such as honoring authentication types and exec/shell/etc requests.

    The bulk of the actual server side logic is handled in the
    ``serve_responses`` function and its ``SSHHandler`` class.
    """
    def __init__(self, user_mapping, pubkeys):
        self.event = threading.Event()
        self.user_mapping = user_mapping
        self.pubkeys = pubkeys
        self.command = None

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return ssh.OPEN_SUCCEEDED
        return ssh.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel, command):
        self.command = command
        self.event.set()
        return True

    def check_channel_pty_request(self, *args):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_auth_password(self, username, password):
        self.username = username
        passed = self.user_mapping.get(username) == password
        return ssh.AUTH_SUCCESSFUL if passed else ssh.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        self.username = username
        return ssh.AUTH_SUCCESSFUL if self.pubkeys.isSet() else ssh.AUTH_FAILED 

    def get_allowed_auths(self, username):
        return 'password,publickey'


class SSHServer(ThreadingMixIn, TCPServer):
    """
    Just a silly empty subclass to make a threading TCP server.
    """
    pass


def serve_responses(mapping, user_mapping, port, pubkeys):
    """
    Return a threading TCP based SocketServer listening on ``port``.

    Used as a fake SSH server which will respond to commands given in
    ``mapping`` and allow connections for users listed in ``user_mapping``.

    ``pubkeys`` is a ``threading.Event`` which will allow public key auth when
    set and disallow it when cleared.
    """
    # Define handler class inline so it can access serve_responses' args
    class SSHHandler(BaseRequestHandler):
        def init_transport(self):
            transport = ssh.Transport(self.request)
            transport.add_server_key(ssh.RSAKey(filename=os.path.join(
                os.path.dirname(__file__),
                'server.key'
            )))
            server = ParamikoServer(user_mapping, pubkeys)
            transport.start_server(server=server)
            self.server = server
            self.transport = transport

        def split_sudo_prompt(self):
            prefix = re.escape(_sudo_prefix(None).rstrip()) + ' +'
            result = re.findall(r'^(%s)?(.*)$' % prefix, self.server.command)[0]
            self.sudo_prompt, self.server.command = result

        def response(self):
            result = mapping[self.server.command]
            stderr = ""
            status = 0
            if isinstance(result, types.StringTypes):
                stdout = result
            else:
                size = len(result)
                if size == 1:
                    stdout = result[0]
                elif size == 2:
                    stdout, stderr = result
                elif size == 3:
                    stdout, stderr, status = result
            stdout, stderr = _equalize((stdout, stderr))
            return stdout, stderr, status

        def sudo_password(self):
            # Give user 3 tries, as is typical
            passed = False
            for x in range(3):
                self.channel.send(env.sudo_prompt)
                password = self.channel.recv(65535).strip()
                # Spit back newline to fake the echo of user's
                # newline
                self.channel.send('\n')
                # Test password
                if password == user_mapping[self.server.username]:
                    passed = True
                    break
                # If here, password was bad.
                self.channel.send("Sorry, try again.\n")
            return passed

        def respond(self):
            for out, err in zip(self.stdout, self.stderr):
                if out is not None:
                    self.channel.send(out)
                if err is not None:
                    self.channel.send_stderr(err)
            self.channel.send_exit_status(self.status)

        def handle(self):
            try:
                self.init_transport()
                self.waiting_for_command = False
                while True:
                    # Don't overwrite channel if we're waiting for a command.
                    if not self.waiting_for_command:
                        self.channel = self.transport.accept(1)
                        if not self.channel:
                            continue
                    self.server.event.wait(10)
                    if self.server.command:
                        # Set self.sudo_prompt, update self.server.command
                        self.split_sudo_prompt()
                        if self.server.command in mapping:
                            self.stdout, self.stderr, self.status = \
                                self.response()
                            if self.sudo_prompt and not self.sudo_password():
                                self.channel.send("sudo: 3 incorrect password attempts\n")
                                break
                            self.respond()
                        else:
                            channel.send_stderr("Sorry, I don't recognize that command.\n")
                            channel.send_exit_status(1)
                        # Close up shop
                        self.server.command = None
                        self.waiting_for_command = False
                        self.channel.close()
                    else:
                        # If we're here, self.server.command was False or None,
                        # but we do have a valid Channel object. Thus we're
                        # waiting for the command to show up.
                        self.waiting_for_command = True
            finally:
                self.transport.close()

    return SSHServer(('localhost', port), SSHHandler)
