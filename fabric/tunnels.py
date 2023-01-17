"""
Tunnel and connection forwarding internals.

If you're looking for simple, end-user-focused connection forwarding, please
see `.Connection`, e.g. `.Connection.forward_local`.
"""

import select
import socket
import time
from threading import Event

from invoke.exceptions import ThreadException
from invoke.util import ExceptionHandlingThread


class TunnelManager(ExceptionHandlingThread):
    """
    Thread subclass for tunnelling connections over SSH between two endpoints.

    Specifically, one instance of this class is sufficient to sit around
    forwarding any number of individual connections made to one end of the
    tunnel or the other. If you need to forward connections between more than
    one set of ports, you'll end up instantiating multiple TunnelManagers.

    Wraps a `~paramiko.transport.Transport`, which should already be connected
    to the remote server.

    .. versionadded:: 2.0
    """

    def __init__(
        self,
        local_host,
        local_port,
        remote_host,
        remote_port,
        transport,
        finished,
    ):
        super().__init__()
        self.local_address = (local_host, local_port)
        self.remote_address = (remote_host, remote_port)
        self.transport = transport
        self.finished = finished

    def _run(self):
        # Track each tunnel that gets opened during our lifetime
        tunnels = []

        # Set up OS-level listener socket on forwarded port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: why do we want REUSEADDR exactly? and is it portable?
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # NOTE: choosing to deal with nonblocking semantics and a fast loop,
        # versus an older approach which blocks & expects outer scope to cause
        # a socket exception by close()ing the socket.
        sock.setblocking(0)
        sock.bind(self.local_address)
        sock.listen(1)

        while not self.finished.is_set():
            # Main loop-wait: accept connections on the local listener
            # NOTE: EAGAIN means "you're nonblocking and nobody happened to
            # connect at this point in time"
            try:
                tun_sock, local_addr = sock.accept()
                # Set TCP_NODELAY to match OpenSSH's forwarding socket behavior
                tun_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except BlockingIOError:  # ie errno.EAGAIN
                # TODO: make configurable
                time.sleep(0.01)
                continue

            # Set up direct-tcpip channel on server end
            # TODO: refactor w/ what's used for gateways
            channel = self.transport.open_channel(
                "direct-tcpip", self.remote_address, local_addr
            )

            # Set up 'worker' thread for this specific connection to our
            # tunnel, plus its dedicated signal event (which will appear as a
            # public attr, no need to track both independently).
            finished = Event()
            tunnel = Tunnel(channel=channel, sock=tun_sock, finished=finished)
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
        sock.close()


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
        super().__init__()

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
