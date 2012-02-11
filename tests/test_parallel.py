from __future__ import with_statement

from fabric.api import run, parallel, env, hide

from utils import FabricTest, eq_
from server import server, RESPONSES


class TestParallel(FabricTest):

    @server()
    @parallel
    def test_parallel(self):
        """
        Want to do a simple call and respond
        """
        env.pool_size = 10
        cmd = "ls /simple"
        with hide('everything'):
            eq_(run(cmd), RESPONSES[cmd])
