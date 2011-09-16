from __future__ import with_statement

from datetime import datetime
import copy
import getpass
import sys

import paramiko
from nose.tools import with_setup
from fudge import (Fake, clear_calls, clear_expectations, patch_object, verify,
    with_patched_object, patched_context, with_fakes)

from fabric.context_managers import settings, hide, show
from fabric.network import (HostConnectionCache, join_host_strings, normalize,
    denormalize)
from fabric.io import output_loop
import fabric.network # So I can call patch_object correctly. Sigh.
from fabric.state import env, output, _get_system_username
from fabric.operations import run, sudo
from fabric.decorators import runs_parallel

from utils import *
from server import (server, PORT, RESPONSES, PASSWORDS, CLIENT_PRIVKEY, USER,
    CLIENT_PRIVKEY_PASSPHRASE)

class TestParallel(FabricTest):

    @server()
    @runs_parallel
    def test_runs_parallel(self):
        """
        Want to do a simple call and respond
        """
        env.pool_size = 10
        cmd = "ls /simple"
        with hide('everything'):
            eq_(run(cmd), RESPONSES[cmd])
