
from utils import FabricTest
from server import server, HOST, PORT

from fabric import native_ssh

class TestNative(FabricTest):

    @server()
    def test_native_sftp(self):
        native = native_ssh.NativeSSHClient()
        native.connect(HOST, port=PORT)
        sftp = native.open_sftp()
        tmp = sftp.open("/tmpaaa", "w")
        tmp.close()
        print repr(sftp.listdir('/'))
        print repr(sftp.stat('/'))

