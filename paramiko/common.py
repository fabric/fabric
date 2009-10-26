# Copyright (C) 2003-2007  Robey Pointer <robey@lag.net>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
Common constants and global variables.
"""

MSG_DISCONNECT, MSG_IGNORE, MSG_UNIMPLEMENTED, MSG_DEBUG, MSG_SERVICE_REQUEST, \
    MSG_SERVICE_ACCEPT = range(1, 7)
MSG_KEXINIT, MSG_NEWKEYS = range(20, 22)
MSG_USERAUTH_REQUEST, MSG_USERAUTH_FAILURE, MSG_USERAUTH_SUCCESS, \
        MSG_USERAUTH_BANNER = range(50, 54)
MSG_USERAUTH_PK_OK = 60
MSG_USERAUTH_INFO_REQUEST, MSG_USERAUTH_INFO_RESPONSE = range(60, 62)
MSG_GLOBAL_REQUEST, MSG_REQUEST_SUCCESS, MSG_REQUEST_FAILURE = range(80, 83)
MSG_CHANNEL_OPEN, MSG_CHANNEL_OPEN_SUCCESS, MSG_CHANNEL_OPEN_FAILURE, \
    MSG_CHANNEL_WINDOW_ADJUST, MSG_CHANNEL_DATA, MSG_CHANNEL_EXTENDED_DATA, \
    MSG_CHANNEL_EOF, MSG_CHANNEL_CLOSE, MSG_CHANNEL_REQUEST, \
    MSG_CHANNEL_SUCCESS, MSG_CHANNEL_FAILURE = range(90, 101)


# for debugging:
MSG_NAMES = {
    MSG_DISCONNECT: 'disconnect',
    MSG_IGNORE: 'ignore',
    MSG_UNIMPLEMENTED: 'unimplemented',
    MSG_DEBUG: 'debug',
    MSG_SERVICE_REQUEST: 'service-request',
    MSG_SERVICE_ACCEPT: 'service-accept',
    MSG_KEXINIT: 'kexinit',
    MSG_NEWKEYS: 'newkeys',
    30: 'kex30',
    31: 'kex31',
    32: 'kex32',
    33: 'kex33',
    34: 'kex34',
    MSG_USERAUTH_REQUEST: 'userauth-request',
    MSG_USERAUTH_FAILURE: 'userauth-failure',
    MSG_USERAUTH_SUCCESS: 'userauth-success',
    MSG_USERAUTH_BANNER: 'userauth--banner',
    MSG_USERAUTH_PK_OK: 'userauth-60(pk-ok/info-request)',
    MSG_USERAUTH_INFO_RESPONSE: 'userauth-info-response',
    MSG_GLOBAL_REQUEST: 'global-request',
    MSG_REQUEST_SUCCESS: 'request-success',
    MSG_REQUEST_FAILURE: 'request-failure',
    MSG_CHANNEL_OPEN: 'channel-open',
    MSG_CHANNEL_OPEN_SUCCESS: 'channel-open-success',
    MSG_CHANNEL_OPEN_FAILURE: 'channel-open-failure',
    MSG_CHANNEL_WINDOW_ADJUST: 'channel-window-adjust',
    MSG_CHANNEL_DATA: 'channel-data',
    MSG_CHANNEL_EXTENDED_DATA: 'channel-extended-data',
    MSG_CHANNEL_EOF: 'channel-eof',
    MSG_CHANNEL_CLOSE: 'channel-close',
    MSG_CHANNEL_REQUEST: 'channel-request',
    MSG_CHANNEL_SUCCESS: 'channel-success',
    MSG_CHANNEL_FAILURE: 'channel-failure'
    }


# authentication request return codes:
AUTH_SUCCESSFUL, AUTH_PARTIALLY_SUCCESSFUL, AUTH_FAILED = range(3)


# channel request failed reasons:
(OPEN_SUCCEEDED,
 OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED,
 OPEN_FAILED_CONNECT_FAILED,
 OPEN_FAILED_UNKNOWN_CHANNEL_TYPE,
 OPEN_FAILED_RESOURCE_SHORTAGE) = range(0, 5)


CONNECTION_FAILED_CODE = {
    1: 'Administratively prohibited',
    2: 'Connect failed',
    3: 'Unknown channel type',
    4: 'Resource shortage'
}


DISCONNECT_SERVICE_NOT_AVAILABLE, DISCONNECT_AUTH_CANCELLED_BY_USER, \
    DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE = 7, 13, 14

from rng import StrongLockingRandomPool

# keep a crypto-strong PRNG nearby
randpool = StrongLockingRandomPool()

import sys
if sys.version_info < (2, 3):
    try:
        import logging
    except:
        import logging22 as logging
    import select
    PY22 = True

    import socket
    if not hasattr(socket, 'timeout'):
        class timeout(socket.error): pass
        socket.timeout = timeout
        del timeout
else:
    import logging
    PY22 = False


DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
