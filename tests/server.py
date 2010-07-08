from __future__ import with_statement
import itertools
import os
import re
import socket
import sys
import threading
import types

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


def serve_responses(mapping, port):
    all_done = threading.Event()
    def inner(mapping, port):
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
            waiting_for_command = False
            while not all_done.isSet():
                # Set timeout to long enough to deal with network hiccups but
                # no so long that final wrapup takes forever.
                # Also, don't overwrite channel if we're waiting for a command.
                if not waiting_for_command:
                    channel = transport.accept(1)
                    if not channel:
                        continue
                server.event.wait(10)

                # SSH! (responding to exec_command())
                if server.command:
                    # Separate out sudo prompt
                    prefix = re.escape(_sudo_prefix(None).rstrip()) + ' +'
                    regex = r'^(%s)?(.*)$' % prefix
                    result = re.findall(regex, server.command)[0]
                    sudo_prompt, server.command = result
                    # Respond to known commands
                    if server.command in mapping:
                        # Parse out response info: (stdout, [stderr, [status]])
                        result = mapping[server.command]
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
                        channel.send_stderr("Sorry, I don't recognize that command.\n")
                        channel.send_exit_status(1)
                    # Close up shop
                    server.command = None
                    waiting_for_command = False
                    channel.close()
                else:
                    # If we're here, server.command was False or None, but we
                    # do have a valid Channel object. Thus we're waiting for
                    # the command to show up.
                    waiting_for_command = True

        finally:
            transport.close()
            sock.close()

    thread = threading.Thread(None, inner, "server", (mapping, port))
    thread.setDaemon(True)
    thread.start()
    return thread, all_done
