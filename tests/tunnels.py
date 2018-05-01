import socket
import struct
import threading

import requests
from mock import patch, Mock, call, ANY
from pytest import raises

from fabric.tunnels import BaseTunnelManager, TunnelManager, SocksTunnelManager


def _local_channel(remote_addr, local_addr):
    return socket.create_connection(remote_addr)


class BaseTunnelManager_:

    @patch('socket.socket')
    def setup(self, socket):
        self.sock = socket.return_value
        self.transport = Mock()
        self.finished = Mock()
        self.mgr = BaseTunnelManager('localhost',
                                     5555,
                                     self.transport,
                                     self.finished)

        # Turn on ultra_debug for code coverage
        self.mgr.ultra_debug = True

    class init:
        "__init__"

        def listens_on_port(self):
            self.sock.bind.assert_called_once_with(('localhost', 5555))
            self.sock.listen.assert_called()

    class reads_and_writes:
        @patch('select.select')
        def read_all_reads_all(self, select):
            sock = Mock()
            select.return_value = ([sock], [], [])
            sock.recv.return_value = bytes(10)

            data = self.mgr._read_all(sock, 100)

            assert len(data) == 100
            assert sock.recv.call_count == 10

        @patch('select.select')
        def read_all_raises_eof(self, select):
            sock = Mock()
            select.return_value = ([sock], [], [])
            sock.recv.return_value = bytes()

            with raises(EOFError):
                self.mgr._read_all(sock, 1)

        @patch.object(BaseTunnelManager, '_read_all')
        def read_struct(self, read_all):
            read_all.return_value = struct.pack('H10s', 42, b'HelloWorld')
            (n, s) = self.mgr._read_struct(Mock(), 'H10s')
            assert n == 42
            assert s == b'HelloWorld'
            read_all.assert_called_with(ANY, 12)

        def send_all_sends_all(self):
            data = struct.pack('100B', *range(100))
            sock = Mock()
            sock.send.return_value = 10

            self.mgr._send_all(sock, data)
            calls = [call(data[n:]) for n in range(0, 100, 10)]
            sock.send.assert_has_calls(calls)

        def send_all_raises_eof(self):
            sock = Mock()
            sock.send.return_value = 0
            with raises(EOFError):
                self.mgr._send_all(sock, b'data')

        @patch.object(BaseTunnelManager, '_send_all')
        def send_struct(self, send_all):
            self.mgr._send_struct(Mock(), 'H10s', 42, b'HelloWorld')
            d = struct.pack('H10s', 42, b'HelloWorld')
            send_all.assert_called_with(ANY, d)

        def handle_accept_not_implemented(self):
            self.finished.is_set.side_effect = iter([False, True])
            tun_sock = Mock()
            self.sock.accept.return_value = (tun_sock, 0)
            with raises(NotImplementedError):
                self.mgr._run()

        @patch.object(BaseTunnelManager, '_handle_accept', return_value=None)
        def handle_accept_called(self, handle_accept):
            self.finished.is_set.side_effect = iter([False, True])
            tun_sock = Mock()
            self.sock.accept.return_value = (tun_sock, 0)
            self.mgr._run()
            handle_accept.assert_called_with(tun_sock, 0)

        def open_channel_opens_direct_tcpip_channel(self):
            r = ('remotehost', 8888)
            l = ('localhost', 5555)
            self.mgr._open_channel(r, l)
            self.transport.assert_call_with('direct-tcpip', r, l)


class TunnelManager_:
    @patch('socket.socket')
    def setup(self, socket):
        self.sock = socket.return_value
        self.transport = Mock()
        self.finished = Mock()
        self.mgr = TunnelManager('localhost',
                                 5555,
                                 'remotehost',
                                 8888,
                                 self.transport,
                                 self.finished)

        # Turn on ultra_debug for code coverage
        self.mgr.ultra_debug = True

    @patch.object(BaseTunnelManager, '_open_channel')
    def handle_accept_opens_channel(self, open_channel):
        self.finished.is_set.side_effect = iter([False, True])
        tun_sock = Mock()
        self.sock.accept.return_value = (tun_sock, 0)
        open_channel.return_value = None

        self.mgr._run()
        open_channel.assert_called_with(('remotehost', 8888), 0)

    @patch.object(BaseTunnelManager, '_open_channel',
                  side_effect=_local_channel)
    def tunnels_ok(self, open_channel, ok_httpserver):
        self.finished.is_set.side_effect = iter([False, True])
        tun_sock = Mock()
        self.sock.accept.return_value = (tun_sock, 0)
        open_channel.return_value = None

        self.mgr._run()
        open_channel.assert_called_with(('remotehost', 8888), 0)


class SocksTunnelManager_:
    class init:
        "__init__"

        @patch('socket.socket')
        @patch('uuid.uuid4')
        def random_auth_is_generated(self, uuid4, socket):
            socket.return_value.getsockname.return_value = ('localhost', 1080)
            uuid4.side_effect = iter(['random1', 'random2'])
            mgr = SocksTunnelManager('localhost', 0, None, None,
                                     authenticate=1)
            assert uuid4.call_count == 2
            assert mgr.authenticate == ('random1', 'random2')

        @patch('socket.socket')
        def given_auth_is_used(self, socket):
            socket.return_value.getsockname.return_value = ('localhost', 1080)
            mgr = SocksTunnelManager('localhost', 0, None, None,
                                     authenticate=('user', 'pass'))
            assert mgr.authenticate == ('user', 'pass')

    class socks4:

        @patch.object(BaseTunnelManager, '_open_channel',
                      side_effect=_local_channel)
        def http_get(self, open_channel, ok_httpserver):
            """Test end-to-end flow. Transport is the only thing mocked."""
            # sanity test our ok_httpserver fixture
            r = requests.get(ok_httpserver.url)
            r.raise_for_status()
            assert r.text == 'ok'

            # start the socks proxy
            mgr = SocksTunnelManager('localhost', 0, Mock(), threading.Event())
            mgr.ultra_debug = True
            mgr.start()

            # use it
            proxy = {'http': mgr.proxy_uri.replace('socks5', 'socks4')}
            r = requests.get(ok_httpserver.url, proxies=proxy)
            r.raise_for_status()
            assert r.text == 'ok'

            # stop the proxy
            mgr.finished.set()
            mgr.join()

            # ensure this now fails with the proxy stopped
            with raises(requests.exceptions.ConnectionError):
                requests.get(ok_httpserver.url, proxies=proxy)

    class socks5:

        @patch.object(BaseTunnelManager, '_open_channel',
                      side_effect=_local_channel)
        def http_get(self, open_channel, ok_httpserver):
            """Test end-to-end flow. Transport is the only thing mocked."""
            # sanity test our ok_httpserver fixture
            r = requests.get(ok_httpserver.url)
            r.raise_for_status()
            assert r.text == 'ok'

            # start the socks proxy
            mgr = SocksTunnelManager('localhost', 0, Mock(),
                                     threading.Event(),
                                     authenticate=False)
            mgr.ultra_debug = True
            mgr.start()

            # use it
            proxy = {'http': mgr.proxy_uri}
            r = requests.get(ok_httpserver.url, proxies=proxy)
            r.raise_for_status()
            assert r.text == 'ok'

            # stop the proxy
            mgr.finished.set()
            mgr.join()

            # ensure this now fails with the proxy stopped
            with raises(requests.exceptions.ConnectionError):
                requests.get(ok_httpserver.url, proxies=proxy)

        @patch.object(BaseTunnelManager, '_open_channel',
                      side_effect=_local_channel)
        def http_get_with_authentication(self, open_channel, ok_httpserver):
            """Test end-to-end flow. Transport is the only thing mocked."""
            # sanity test our ok_httpserver fixture
            r = requests.get(ok_httpserver.url)
            r.raise_for_status()
            assert r.text == 'ok'

            # start the socks proxy
            mgr = SocksTunnelManager('localhost', 0, Mock(),
                                     threading.Event(),
                                     authenticate=True)
            mgr.ultra_debug = True
            mgr.start()

            # use it
            proxy = {'http': mgr.proxy_uri}
            r = requests.get(ok_httpserver.url, proxies=proxy)
            r.raise_for_status()
            assert r.text == 'ok'

            # stop the proxy
            mgr.finished.set()
            mgr.join()

            # ensure this now fails with the proxy stopped
            with raises(requests.exceptions.ConnectionError):
                requests.get(ok_httpserver.url, proxies=proxy)
