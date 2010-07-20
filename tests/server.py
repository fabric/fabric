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


class ParamikoServer(ssh.ServerInterface):
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
        logging.debug("Got exec request w/ command: '%s'" % command)
        self.command = command
        self.event.set()
        return True

    def check_channel_pty_request(self, *args):
        return True

    def check_channel_shell_request(self, channel):
        logging.debug("Got shell request")
        self.event.set()
        return True

    def check_auth_password(self, username, password):
        logging.debug("Password auth: %s:%s" % (username, password))
        self.username = username
        passed = self.user_mapping.get(username) == password
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


class SSHServer(ThreadingMixIn, TCPServer):
    def __init__(self, *args, **kwargs):
        self.timeout = 5
        return TCPServer.__init__(self, *args, **kwargs)

    def get_request(self):
        logging.debug("##### lol getting request")
        ret = TCPServer.get_request(self)
        logging.debug("##### whee got request")
        return ret

    def handle_timeout(self):
        logging.debug("############### lol, timed out")


def serve_responses(mapping, user_mapping, port, pubkeys):
    # Define handler class (inline so it can access serve_responses' args)
    class SSHHandler(BaseRequestHandler):
        def handle(self):
            try:
                # More networking!
                logging.debug("[%s] top of handle()" % id(self))
                transport = ssh.Transport(self.request)
                logging.debug("[%s] got transport" % id(self))
                transport.add_server_key(ssh.RSAKey(filename=os.path.join(
                    os.path.dirname(__file__),
                    'server.key'
                )))
                server = ParamikoServer(user_mapping, pubkeys)
                logging.debug("[%s] got paramiko server" % id(self))
                transport.start_server(server=server)
                logging.debug("[%s] started paramiko server" % id(self))

                # Looping!
                waiting_for_command = False
                logging.debug("[%s] Entering main loop" % id(self))
                while True:
                    logging.debug("[%s] Top of loop" % id(self))
                    # Set timeout to long enough to deal with network hiccups but
                    # no so long that final wrapup takes forever.
                    # Also, don't overwrite channel if we're waiting for a command.
                    if not waiting_for_command:
                        logging.debug("[%s] Waiting for a new channel from client" % id(self))
                        channel = transport.accept(1)
                        if not channel:
                            logging.debug("[%s] No channel found" % id(self))
                            continue
                        else:
                            logging.debug("New client channel obtained")
                    else:
                        logging.debug("Waiting for command")
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
            except BaseException, e:
                logging.debug("ZOMG EXCEPTION: %s" % e)
            finally:
                logging.debug("Closing Paramiko transport object")
                transport.close()
            logging.debug("[%s] bottom of handle()" % id(self))

    return SSHServer(('localhost', port), SSHHandler)
