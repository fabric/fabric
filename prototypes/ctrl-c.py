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
import select
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



def posix_shell(chans):
    cmd_buf = ''
    chan_bufs = {}
    selector_list = [sys.stdin]
    for chan in chans:
        chan_bufs[chan.get_name()] = ''
        chan.settimeout(0.0)
        selector_list.append(chan)
    while True:
        if len(chans) == 0:
            break
        r, w, e = select.select(selector_list, [], [])
        for chan in chans:
            if chan in r:
                try:
                    x = chan.recv(1024)
                    name = chan.get_name()
                    if len(x) == 0:
                        selector_list.remove(chan)
                        chans.remove(chan)
                        if len(chans) == 0:
                            break
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
        if reduce(lambda x,y: x and y.endswith("$") or y.endswith("#"), map(str.strip, chan_bufs.values()), True):
            sys.stdout.write("fab$ ")
            sys.stdout.flush()
            for chan in chans:
                chan.status_event.clear()
        if sys.stdin in r:
            x = sys.stdin.readline()
            if len(x) == 0:
                break # stop while True on ctrl-D
            if x != '\n':
                for chan in chans:
                    chan.status_event.clear()
                    chan.sendall(x)


try:
    port = 22
    username = "UNWIRE\\cvh" #raw_input("Username: ")
    password = getpass.getpass()
    ctor = paramiko.SSHClient
    clients = [ctor(), ctor(), ctor()]
    hosts = ['conan.unwire.dk', 'gekko.unwire.dk', 'atlas.unwire.dk']
    channels = []
#    termcap = "dumb"
    termcap = "ansi" # we don't really support the cursor-pos in this, but it has color
    for num, client in enumerate(clients):
        hostname = hosts[num]
        client.load_system_host_keys()
        client.connect(hostname, port, username, password)
        channel = client.invoke_shell(termcap)
        channel.set_name(hostname)
        channel.setblocking(False)
        channels.append(channel)
    posix_shell(channels)
except:
    sys.excepthook(*sys.exc_info())
finally:
    for client in clients:
        client.close()
