from __future__ import with_statement

from fabric.api import run, parallel, env, hide, execute

from utils import FabricTest, eq_, aborts
from server import server, RESPONSES


class OhNoesException(Exception): pass


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

    @server(port=2200)
    @server(port=2201)
    @aborts
    def test_parallel_failures(self):
        with hide('everything'):
            @parallel
            def mytask():
                run("ls /")
                raise OhNoesException
            
            execute(mytask, hosts=['127.0.0.1:2200', '127.0.0.1:2201'])
