"""
Native SSH client wrapper
"""

import subprocess, select, ssh, socket, sys

class NativeSSHClient:
    '''A wrapper around the OpenSSH command line program
       with an interface similar to paramiko SSH

       Uses a persistant background connection
       (a feature of OpenSSH)
    '''

    def __init__(self, debug=False, abort_on_prompts=False):
        self.cmd = None
        self.combine_stderr = False
        self.use_pty = False
        self.debug_on = debug
        self.abort_on_prompts = abort_on_prompts

    def connect(self,
            hostname,
            port=None,
            username=None,
            password=None,
            key_filename=None,
            timeout=10,
            allow_agent=True,
            look_for_keys=True):
        '''start a remote session in the background'''
        self.hostname = hostname
        self.timeout = timeout
        self.port = port
        self.username = username
        self.key_filename = key_filename

        if password != None:
            self._debug('warning: ignoring password for %s@%s: %s',
                    username, hostname, password)

        if subprocess.call(self._args('-AN', '-Ocheck'),
                stderr=open("/dev/null", "w")) != 0:
            if subprocess.call(self._args('-AMfN')) != 0:
                raise ssh.SSHException('Error Connecting')

    # for executing remote commands

    def set_combine_stderr(self, combine):
        self.combine_stderr = combine

    def get_pty(self, term='vt100', width=80, height=24):
        '''chooses between the -tt/-T flags on SSH'''
        self.use_pty = True

    def exec_command(self, command):
        '''run a remote command - returns nothing

        Only a single remote command can run per instance.
        '''
        if self.cmd:
            self.close()

        self.cmd = subprocess.Popen(
                self._args("-tt" if self.use_pty else "-T", command),
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT if self.combine_stderr else subprocess.PIPE,
                )

    # for interacting with the remote command

    def sendall(self, data):
        assert self.cmd
        self.cmd.stdin.write(data)

    def recv(self, nbytes):
        assert self.cmd
        return self._read(self.cmd.stdout, nbytes)

    def recv_stderr(self, nbytes):
        assert self.cmd
        if self.combine_stderr:
            return ""
        else:
            return self._read(self.cmd.stderr, nbytes)

    def exit_status_ready(self):
        assert self.cmd
        self.cmd.poll()
        return self.cmd.returncode != None

    def recv_exit_status(self):
        assert self.cmd
        return self.cmd.returncode

    def close(self):
        '''kills the current command'''
        if self.cmd and self.cmd.poll() == None:
            self.cmd.stdin.close()
            self.cmd.stdout.close()
            if not self.combine_stderr:
                self.cmd.stderr.close()
            self.cmd.kill()

    # SFTP

    def open_sftp(self):
        '''Return a new SFTP socket wrapped in the python SFTPClient'''
        pair = socket.socketpair()
        proc = subprocess.Popen(
                self._args('-s', 'sftp'),
                stdout = pair[1],
                stdin = pair[1],
                )

        sock = SocketChannel(pair[0], 'sftp subsystem')
        return ssh.sftp_client.SFTPClient(sock)

    # internal

    def _args(self, *extra):
        '''Generate the arguments for a command-line call'''
        args=[ 'ssh', '-q' ]

        if self.port:
            args += [ '-p', str(self.port) ]
        if self.username:
            args += [ '-l', self.username ]
        if self.key_filename:
            args += [ '-i' ] + self.key_filename

        if self.abort_on_prompts:
            args += [
                    '-oPasswordAuthentication=no',
                    '-oKbdInteractiveAuthentication=no',
                    ]

        args += [ self.hostname ]
        args += extra

        self._debug('exec %s', " ".join(args))
        return args

    def _read(self, pipe, nbytes):
        ret = select.select([pipe], [], [pipe], self.timeout)
        if ret[0] != [pipe]:
            raise socket.timeout()

        return pipe.read(nbytes)

    def _debug(self, msg, *args):
        if self.debug_on:
            print >>sys.stderr, '[ssh] ' + msg % args

    # obsolete calls that do nothing

    def load_system_host_keys(self):
        '''do nothing - this is set in ~/.ssh/config'''
        pass

    def set_missing_host_key_policy(self, policy):
        '''do nothing - this is set in ~/.ssh/config'''
        pass

    def get_transport(self):
        '''only returns self - this abstraction doesn't apply'''
        return self

    def set_keepalive(self, keepalive):
        '''do nothing - this is set in ~/.ssh/config'''
        pass

    def open_session(self):
        '''only returns self - this abstraction doesn't apply'''
        return self

class SocketChannel(object):
    '''
    A thin wrapper around a socket that includes
    a name and a recv_ready() call. This interface
    is required by the ssh.sftp_client package.
    '''
    def __init__(self, sock, name):
        self.name = name
        self.sock = sock

    def get_name(self):
        return self.name

    def recv_ready(self):
        '''Return True if recv() will not block'''
        ok = select.select([self.sock], [], [], 0)
        return self.sock in ok[0]

    def __getattr__(self, name):
        '''proxy remaining calls to a real socket object'''
        return getattr(self.sock, name)
