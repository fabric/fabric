from __future__ import with_statement
import itertools
import os
import re
import socket
import sys
import threading

import paramiko

from fabric.operations import _sudo_prefix
from fabric.api import env

def _log(txt):
    with open('/tmp/fablog', 'a') as fd:
        fd.write(txt + '\n')


class Server (paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

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
        return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return 'password,publickey'


def _equalize(lists, fillval=None):
    lists = map(list, lists)
    upper = max(len(x) for x in lists)
    for lst in lists:
        diff = upper - len(lst)
        if diff:
            lst.extend([fillval] * diff)
    return lists


def serve_response(expected, stdout, stderr="", status=0, port=2200):
    def inner(expected, stdout, stderr, status, port):
        # Networking!
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        sock.listen(100)
        client, addr = sock.accept()

        try:
            # More networking!
            transport = paramiko.Transport(client)
            transport.add_server_key(paramiko.RSAKey(filename=os.path.join(
                os.path.dirname(__file__),
                'server.key'
            )))
            server = Server()
            transport.start_server(server=server)

            # Looping!
            while transport.is_active():
                _log('top of transport')
                # Wait 3 seconds for a new channel to be opened by the client,
                # before terminating. Should be long enough to handle running a
                # number of tests in between ones that use this server, but not
                # so long that we have to wait forever once everything is done.
                channel = transport.accept(3)
                if not channel:
                    _log('no channel')
                    break
                _log('channel')
                server.event.wait(10)

                # SSH! (responding to exec_command())
                if server.command:
                    _log('got cmd: %s' % server.command)
                    # Separate out sudo prompt
                    prefix = re.escape(_sudo_prefix(None).rstrip()) + ' +'
                    regex = r'^(%s)?(.*)$' % prefix
                    result = re.findall(regex, server.command)[0]
                    sudo_prompt, server.command = result
                    # Respond to known commands
                    if server.command == expected:
                        # Send prompt, wait for response, if sudo detected
                        if sudo_prompt:
                           channel.send(env.sudo_prompt)
                           channel.recv(65535)
                           # Spit back newline to fake the echo of user's
                           # newline
                           channel.send('\n')
                        # Send command output, exit status
                        stdout, stderr = _equalize((stdout, stderr))
                        for out, err in zip(stdout, stderr):
                            if out is not None:
                                channel.send(out)
                            if err is not None:
                                channel.send_stderr(err)
                        channel.send_exit_status(status)
                    # Error out if command unknown
                    else:
                        channel.send("Sorry, I don't recognize that command.\n")
                        channel.send("Expected '%s', got '%s'" % (expected,
                            server.command))
                        channel.send_exit_status(1)
                    # Close up shop
                    _log('closing channel')
                    channel.close()

        finally:
            _log('finishing')
            transport.close()
            sock.close()

    thread = threading.Thread(None, inner, "server", (expected, stdout, stderr,
        status, port))
    thread.setDaemon(True)
    thread.start()
    return thread
