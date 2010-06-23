import itertools
import os
import re
import socket
import sys
import threading

import paramiko

from fabric.operations import _sudo_prefix
from fabric.api import env


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


def serve_response(expected, stdout, stderr="", status=0):
    def inner(expected, stdout, stderr, status):
        # Set up socket on high numbered port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 2200))

        # Listen for an incoming connection
        sock.listen(100)
        client, addr = sock.accept()

        # Perform SSH stuff on the connection
        try:
            t = paramiko.Transport(client)
            t.add_server_key(paramiko.RSAKey(filename=os.path.join(
                os.path.dirname(__file__),
                'server.key'
            )))
            server = Server()
            t.start_server(server=server)

            # wait for auth
            chan = t.accept(20)
            server.event.wait(10)
            # Perform actual interaction logic
            if server.command:
                # Handle sudo
                prefix = _sudo_prefix(None)
                regex = r'^(%s)?(.*)$' % (re.escape(prefix.rstrip()) + ' +')
                result = re.findall(regex, server.command)[0]
                sudo_prompt, server.command = result
                if server.command == expected:
                    if sudo_prompt:
                       chan.send(env.sudo_prompt)
                       chan.recv(65535)
                    # Actual output loop
                    stdout, stderr = _equalize((stdout, stderr))
                    for out, err in zip(stdout, stderr):
                        if out is not None:
                            chan.send(out)
                        if err is not None:
                            chan.send_stderr(err)
                    chan.send_exit_status(status)
                else:
                    chan.send("Sorry, I don't recognize that command.\n")
                    chan.send("Expected '%s', got '%s'" % (expected,
                        server.command))
                    chan.send_exit_status(0)

            chan.close()

        except Exception, e:
            t.close()
            raise e

    thread = threading.Thread(None, inner, "server", (expected, stdout, stderr,
        status))
    thread.setDaemon(True)
    thread.start()
    return thread
