import unittest
from functools import partial

import paramiko as ssh

class SSHServerMock(ssh.ServerInterface):
    pass

