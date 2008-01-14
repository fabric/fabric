#!/usr/bin/env python

# Fabric - Pythonic remote deployment tool.
# Copyright (C) 2008  Christian Vest Hansen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import getpass
import socket
import sys

# windows does not have termios...
try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False

import paramiko



def posix_shell(prompt, *chans):
    import select
    
    #oldtty = termios.tcgetattr(sys.stdin)
    cmd_buf = ''
    chan_bufs = {}
    for chan in chans:
        chan_bufs[chan.get_name()] = ''
    try:
        #tty.setraw(sys.stdin.fileno())
        #tty.setcbreak(sys.stdin.fileno())
        for chan in chans:
            chan.settimeout(0.0)
        selector_list = [sys.stdin]
        for chan in chans:
            selector_list.append(chan)
        while True:
            r, w, e = select.select(selector_list, [], [])
            for chan in chans:
                if chan in r:
                    try:
                        x = chan.recv(1024)
                        name = chan.get_name()
                        if len(x) == 0:
                            print '\r\n*** EOF\r\n',
                            return
                        x = x.replace('\n', '\n[%s] ' % name)
                        output = chan_bufs[name] + x
                        lines = output.splitlines()
                        if len(lines) > 1 and output.endswith('\n'):
                            for line in lines:
                                tpl = (name, line)
                                sys.stdout.write('[%s] %s\n' % tpl)
                            chan_bufs[name] = ''
                        elif len(lines) > 1:
                            for line in lines[:-1]:
                                tpl = (name, line)
                                sys.stdout.write('[%s] %s\n' % tpl)
                            chan_bufs[name] = lines[-1]
                        else:
                            chan_bufs[name] = output
                        sys.stdout.flush()
                    except socket.timeout:
                        pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                #sys.stdout.write(x)
                cmd_buf += x
                if x == '\n':
                    sys.stdout.write(prompt)
                    #selector_list = [sys.stdin]
                    for chan in chans:
                        stdin, stdout, stderr = chan.exec_command(cmd_buf)
                        #stdout.get_name = (lambda: chan.get_name() + ' out')
                        #stderr.get_name = (lambda: chan.get_name() + ' err')
                        #selector_list.append(stdout)
                        #selector_list.append(stderr)
                    cmd_buf = ''
                sys.stdout.flush()
    finally:
        pass
        #termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


try:
    port = 22
    username = "UNWIRE\\cvh" #raw_input("Username: ")
    password = getpass.getpass()
    ctor = paramiko.SSHClient
    clients = [ctor(), ctor(), ctor()]
    hosts = ['conan.unwire.dk', 'gekko.unwire.dk', 'atlas.unwire.dk']
    channels = []
    for num, client in enumerate(clients):
        hostname = hosts[num]
        client.load_system_host_keys()
        client.connect(hostname, port, username, password)
        channel = client.invoke_shell()
        channel.set_name(hostname + ' out')
        channel.setblocking(False)
        channels.append(channel)
    posix_shell("fab> ", *channels)
except:
    sys.excepthook(*sys.exc_info())
finally:
    for client in clients:
        client.close()
