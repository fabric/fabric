from __future__ import with_statement
import itertools
import logging
import os
import re
import socket
import sys
import threading
import types

import paramiko as ssh

from fabric.operations import _sudo_prefix
from fabric.api import env


logging.basicConfig(
    filename='/tmp/test_server.log',
    level=logging.DEBUG,
    datefmt='%H:%M:%S',
    format='[%(asctime)s] %(levelname)-8s %(message)s'
)


class Server(ssh.ServerInterface):
    def __init__(self, user_mapping, pubkeys):
        self.event = threading.Event()
        self.user_mapping = user_mapping
        self.pubkeys = pubkeys

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return ssh.OPEN_SUCCEEDED
        return ssh.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_exec_request(self, channel, command):
        logging.debug("Got exec request w/ command: '%s'" % command)
        self.command = command
        self.event.set()
        return True

    def check_channel_pty_request(self, *args):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_auth_password(self, username, password):
        logging.debug("Password auth: %s:%s" % (username, password))
        self.username = username
        passed = self.user_mapping[username] == password
        return ssh.AUTH_SUCCESSFUL if passed else ssh.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        logging.debug("Pubkey auth: %s" % username)
        self.username = username
        return ssh.AUTH_SUCCESSFUL if self.pubkeys.isSet() else ssh.AUTH_FAILED 

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


def serve_responses(mapping, user_mapping, port, pubkeys, all_done):
    # Networking!
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.listen(100)
    client, addr = sock.accept()

    try:
        # More networking!
        transport = ssh.Transport(client)
        transport.add_server_key(ssh.RSAKey(filename=os.path.join(
            os.path.dirname(__file__),
            'server.key'
        )))
        server = Server(user_mapping, pubkeys)
        transport.start_server(server=server)

        # Looping!
        waiting_for_command = False
        logging.debug("Entering main loop")
        while not all_done.isSet():
            logging.debug("Top of loop")
            # Set timeout to long enough to deal with network hiccups but
            # no so long that final wrapup takes forever.
            # Also, don't overwrite channel if we're waiting for a command.
            if not waiting_for_command:
                logging.debug("Waiting for a new client to connect")
                channel = transport.accept(1)
                if not channel:
                    logging.debug("No client found")
                    continue
                else:
                    logging.debug("Client channel obtained")
            server.event.wait(10)

            # SSH! (responding to exec_command())
            if server.command:
                logging.debug("In loop, see server command '%s'" %
                        server.command)
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
                        # Give user 3 tries, as is typical
                        passed = False
                        for x in range(3):
                            channel.send(env.sudo_prompt)
                            password = channel.recv(65535).strip()
                            # Spit back newline to fake the echo of user's
                            # newline
                            channel.send('\n')
                            # Test password
                            if password == user_mapping[server.username]:
                                passed = True
                                break
                            # If here, password was bad.
                            channel.send("Sorry, try again.\n")
                        if not passed:
                            channel.send("sudo: 3 incorrect password attempts\n")
                            break # out of outer loop
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
        logging.debug("In finally block")
        transport.close()
        sock.close()
        logging.debug("Closed socket, transport")
