import binascii
import errno
import logging
import select
import socket
import struct
import time
import uuid
from threading import Event

from invoke.exceptions import ThreadException
from invoke.util import ExceptionHandlingThread
from paramiko.util import format_binary


class TunnelError(Exception):
    pass


class SocksError(TunnelError):
    pass


class BaseTunnelManager(ExceptionHandlingThread):
    def __init__(self,
                 local_host, local_port,
                 transport, finished
                 ):
        super(BaseTunnelManager, self).__init__()
        self.ultra_debug = False
        self.log = logging.getLogger('fabric.tunnels')
        self.transport = transport
        self.finished = finished

        # Set up OS-level listener socket on forwarded port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: why do we want REUSEADDR exactly? and is it portable?
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # NOTE: choosing to deal with nonblocking semantics and a fast loop,
        # versus an older approach which blocks & expects outer scope to cause
        # a socket exception by close()ing the socket.
        self.sock.setblocking(0)
        self.sock.bind((local_host, local_port))
        self.local_address = self.sock.getsockname()
        self.sock.listen(1)
        self.log.debug("listening on {}".format(self.local_address))

    def _run(self):
        # Track each tunnel that gets opened during our lifetime
        tunnels = []

        while not self.finished.is_set():
            # Main loop-wait: accept connections on the local listener
            # NOTE: EAGAIN means "you're nonblocking and nobody happened to
            # connect at this point in time"
            try:
                tun_sock, local_addr = self.sock.accept()
                # Set TCP_NODELAY to match OpenSSH's forwarding socket behavior
                tun_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except socket.error as e:
                if e.errno is errno.EAGAIN:
                    # TODO: make configurable
                    time.sleep(0.01)
                    continue
                raise

            channel = None
            try:
                channel = self._handle_accept(tun_sock, local_addr)
            except TunnelError:
                self.log.debug("tunnel exception.", exc_info=True)

            if not channel:
                tun_sock.close()
            else:
                # Set up 'worker' thread for this specific connection to our
                # tunnel, plus its dedicated signal event (which will appear as
                # public attr, no need to track both independently).
                finished = Event()
                tunnel = Tunnel(channel=channel,
                                sock=tun_sock,
                                finished=finished)
                tunnel.start()
                tunnels.append(tunnel)

        exceptions = []
        # Propogate shutdown signal to all tunnels & wait for closure
        # TODO: would be nice to have some output or at least logging here,
        # especially for "sets up a handful of tunnels" use cases like
        # forwarding nontrivial HTTP traffic.
        for tunnel in tunnels:
            tunnel.finished.set()
            tunnel.join()
            wrapper = tunnel.exception()
            if wrapper:
                exceptions.append(wrapper)
        # Handle exceptions
        if exceptions:
            raise ThreadException(exceptions)

        # All we have left to close is our own sock.
        # TODO: use try/finally?
        self.sock.close()

    def _open_channel(self, remote_addr, local_addr):
        # Set up direct-tcpip channel on server end
        # TODO: refactor w/ what's used for gateways
        self.log.debug("establishing channel to {}:{}".format(*remote_addr))
        return self.transport.open_channel(
            'direct-tcpip',
            remote_addr,
            local_addr,
        )

    def _handle_accept(self, sock, addr):
        raise NotImplementedError()

    def _send_all(self, sock, out):
        if self.ultra_debug:
            for l in format_binary(out, 'OUT: '):
                self.log.debug(l)
        while len(out) > 0:
            n = sock.send(out)
            if n <= 0:
                raise EOFError()
            if n == len(out):
                return
            out = out[n:]
        return

    def _send_struct(self, sock, fmt, *args):
        self._send_all(sock, struct.pack(fmt, *args))

    def _read_all(self, sock, n):
        out = bytes()
        while n > 0:
            while True:
                read, write, err = select.select([sock], [], [], 0.1)
                if len(read) > 0:
                    x = sock.recv(n)
                    break

            if len(x) == 0:
                raise EOFError()
            out += x
            n -= len(x)
        if self.ultra_debug:
            for l in format_binary(out, 'IN: '):
                self.log.debug(l)
        return out

    def _read_struct(self, sock, fmt):
        n = struct.calcsize(fmt)
        data = self._read_all(sock, n)
        return struct.unpack(fmt, data)


class TunnelManager(BaseTunnelManager):
    def __init__(self,
                 local_host, local_port,
                 remote_host, remote_port,
                 transport, finished
                 ):
        super(TunnelManager, self).__init__(local_host, local_port,
                                            transport, finished)
        self.remote_address = (remote_host, remote_port)

    def _handle_accept(self, sock, addr):
        """Create and return a channel to the remote_address."""
        try:
            return self._open_channel(self.remote_address, addr)
        except Exception as e:
            raise TunnelError("exception ({}) while opening channel".format(e))


SOCKS4_VERSION = 4
SOCKS5_VERSION = 5
RESERVED = 0

AUTH_VERSION = 1
AUTH_NONE, AUTH_GSSAPI, AUTH_USERNAME_PASSWORD = range(3)
AUTH_NO_ACCEPTABLE_METHODS = 0xFF

COMMAND_CONNECT, COMMAND_BIND, COMMAND_UDP_ASSOCIATE = range(1, 4)

ATYP_IPV4, _, ATYP_DOMAINNAME, ATYP_IPV6 = range(1, 5)

REPLY_SUCCEEDED, REPLY_GENERAL_FAILURE, REPLY_NOT_ALLOWED, \
    REPLY_NETWORK_UNREACHABLE, REPLY_HOST_UNREACHABLE, \
    REPLY_CONNECTION_REFUSED, REPLY_TTL_EXPIRED, REPLY_COMMAND_NOT_SUPPORTED, \
    REPLY_ATYP_NOT_SUPPORTED = range(9)

REPLY_REQUEST_GRANTED, REPLY_REJECTED_OR_FAILED = range(90, 92)


class SocksTunnelManager(BaseTunnelManager):
    """A Socks 4/5 proxy that channels connections through a transport.

    Supports the CONNECT command with or without username/password
    authentication. Does not support the BIND or UDP ASSOCIATE commands.

    .. versionadded:: 2.0
    """

    def __init__(self,
                 local_host, local_port,
                 transport, finished,
                 authenticate=None,
                 ):
        super(SocksTunnelManager, self).__init__(local_host, local_port,
                                                 transport, finished)
        if authenticate and isinstance(authenticate, tuple):
            self.authenticate = authenticate
        elif authenticate:
            self.authenticate = (str(uuid.uuid4()), str(uuid.uuid4()))
        else:
            self.authenticate = None

        self.proxy_uri = "socks5://{}{}:{}".format(
            "{}:{}@".format(*self.authenticate) if authenticate else '',
            *self.local_address)

    def _handle_accept(self, sock, addr):
        """Dialog with client to authenticate and create remote channel."""
        # Reference: SOCKS5 https://tools.ietf.org/html/rfc1928
        #            SOCSK4 https://www.openssh.com/txt/socks4.protocol
        v, = self._read_struct(sock, '!B')

        if v == SOCKS4_VERSION:
            if not self.authenticate:
                return self._handle_socks4(sock, addr)
            else:
                msg = 'socks4 protocol unsupported with authentication'
                raise SocksError(msg)
        elif v == SOCKS5_VERSION:
            return self._handle_socks5(sock, addr)
        else:
            raise SocksError("unsupported socks version {}".format(v))

    def _handle_socks4(self, sock, addr):
        command, = self._read_struct(sock, '!B')
        if command != COMMAND_CONNECT:
            raise SocksError("unsupported socks command {}".format(command))

        dst_port, = self._read_struct(sock, '!H')
        dst_bytes = self._read_struct(sock, '!BBBB')
        dst = '.'.join(str(x) for x in dst_bytes)

        while self._read_struct(sock, '!B')[0] != 0:
            # consume the userid, which is null terminated.
            pass

        response_code = REPLY_REQUEST_GRANTED
        try:
            return self._open_channel((dst, dst_port), addr)
        except Exception as e:
            response_code = REPLY_REJECTED_OR_FAILED
            raise SocksError("exception ({}) while opening channel".format(e))
        finally:
            self._send_struct(sock, '!BBHBBBB',
                              0, response_code, dst_port, *dst_bytes)

    def _handle_socks5(self, sock, addr):
        self._handle_auth(sock)

        v, command, _ = self._read_struct(sock, '!BBB')
        if v != SOCKS5_VERSION:
            raise SocksError("unsupported socks version {}".format(v))

        if command == COMMAND_CONNECT:
            return self._handle_connect(sock, addr)
        else:
            self._send_struct(sock, '!BBB',
                              SOCKS5_VERSION, REPLY_COMMAND_NOT_SUPPORTED,
                              RESERVED)
            raise SocksError("unsupported socks command {}".format(command))

    def _handle_connect(self, sock, addr):
        dst, addr_data = self._handle_atyp(sock)
        dst_port, = self._read_struct(sock, '!H')

        response_code = REPLY_SUCCEEDED
        try:
            return self._open_channel((dst, dst_port), addr)
        except Exception as e:
            response_code = REPLY_GENERAL_FAILURE
            raise SocksError("exception ({}) while opening channel".format(e))
        finally:
            self._send_struct(sock, '!BBB',
                              SOCKS5_VERSION, response_code, RESERVED)
            self._send_all(sock, addr_data)
            self._send_struct(sock, '!H', dst_port)

    def _handle_atyp(self, sock):
        atyp, = self._read_struct(sock, '!B')
        if atyp == ATYP_IPV4:
            addr_data = self._read_all(sock, 4)
            dst = '.'.join(str(x) for x in struct.unpack('!4B', addr_data))
        elif atyp == ATYP_IPV6:
            addr_data = self._read_all(sock, 16)
            dst = struct.unpack('!8H', addr_data)
            dst = ':'.join(binascii.hexlify(x) for x in dst)
        elif atyp == ATYP_DOMAINNAME:
            dst_len, = self._read_struct(sock, '!B')
            dst, = self._read_struct(sock, "!{}s".format(dst_len))
            addr_data = struct.pack("!B{}s".format(dst_len), dst_len, dst)
        else:
            self._send_struct(sock, '!BBB',
                              SOCKS5_VERSION, REPLY_ATYP_NOT_SUPPORTED,
                              RESERVED)
            raise SocksError("unsupported socks address type {}".format(atyp))
        return dst, struct.pack('!B', atyp) + addr_data

    def _handle_auth(self, sock):
        """Handle authentication of a socks request.

        :param sock: The socket with the client
        :return: True if the request is authenticated, False otherwise
        """

        # Reference: https://tools.ietf.org/html/rfc1929
        auth_methods_length, = self._read_struct(sock, '!B')
        methods = self._read_struct(
            sock, "!{}B".format(auth_methods_length)
        )

        if not self.authenticate and AUTH_NONE in methods:
            self._send_struct(sock, '!BB', SOCKS5_VERSION, AUTH_NONE)
            return

        # Require username/password authentication.
        if AUTH_USERNAME_PASSWORD not in methods:
            self._send_struct(sock, '!B', AUTH_NO_ACCEPTABLE_METHODS)
            raise SocksError('rejecting socks auth as client does not accept'
                             ' user/pass.')

        self._send_struct(sock, '!BB', SOCKS5_VERSION, AUTH_USERNAME_PASSWORD)

        # Read and parse username/password data
        v, username_length = self._read_struct(sock, '!BB')
        if v != AUTH_VERSION:
            raise SocksError('bad socks auth version from client')

        username, password_length = self._read_struct(sock,
                                                      "!{}sB".format(
                                                          username_length))

        password, = self._read_struct(sock,
                                      "{}s".format(password_length))

        if (username.decode(), password.decode()) != self.authenticate:
            self._send_struct(sock, '!BB',
                              AUTH_VERSION, REPLY_GENERAL_FAILURE)
            raise SocksError('socks username/password mismatch')

        self._send_struct(sock, '!BB', AUTH_VERSION, REPLY_SUCCEEDED)
        self.log.debug('socks auth succeeded')

    def _wait(self, sock):
        """Wait for data to be ready to read."""
        select.select([sock], [], [])
        return sock


class Tunnel(ExceptionHandlingThread):
    """
    Bidirectionally forward data between an SSH channel and local socket.

    .. versionadded:: 2.0
    """

    def __init__(self, channel, sock, finished):
        self.channel = channel
        self.sock = sock
        self.finished = finished
        self.socket_chunk_size = 1024
        self.channel_chunk_size = 1024
        super(Tunnel, self).__init__()

    def _run(self):
        try:
            empty_sock, empty_chan = None, None
            while not self.finished.is_set():
                r, w, x = select.select([self.sock, self.channel], [], [], 1)
                if self.sock in r:
                    empty_sock = self.read_and_write(
                        self.sock, self.channel, self.socket_chunk_size
                    )
                if self.channel in r:
                    empty_chan = self.read_and_write(
                        self.channel, self.sock, self.channel_chunk_size
                    )
                if empty_sock or empty_chan:
                    break
        finally:
            self.channel.close()
            self.sock.close()

    def read_and_write(self, reader, writer, chunk_size):
        """
        Read ``chunk_size`` from ``reader``, writing result to ``writer``.

        Returns ``None`` if successful, or ``True`` if the read was empty.

        .. versionadded:: 2.0
        """
        data = reader.recv(chunk_size)
        if len(data) == 0:
            return True
        writer.sendall(data)
