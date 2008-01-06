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

import sys
import getpass

import paramiko

client = paramiko.SSHClient()
try:
    client.load_system_host_keys()
    hostname = raw_input("Hostname: ")
    port = 22
    username = raw_input("Username: ")
    password = getpass.getpass()
    
    client.connect(hostname, port, username, password)
    
    cmd = raw_input("[%s@%s]$ " % (username, hostname))
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in stdout:
        print line,
except:
    sys.excepthook(*sys.exc_info())
finally:
    client.close()
