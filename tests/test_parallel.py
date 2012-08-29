from __future__ import with_statement

from fabric.api import run, parallel, env, hide, execute, settings

from utils import FabricTest, eq_, aborts, mock_streams
from server import server, RESPONSES

# TODO: move this into test_tasks? meh.


class OhNoesException(Exception):
    pass


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
    def test_parallel_failures_abort(self):
        with hide('everything'):
            host1 = '127.0.0.1:2200'
            host2 = '127.0.0.1:2201'

            @parallel
            def mytask():
                run("ls /")
                if env.host_string == host2:
                    raise OhNoesException

            execute(mytask, hosts=[host1, host2])

    @server(port=2200)
    @server(port=2201)
    @mock_streams('stderr')  # To hide the traceback for now
    def test_parallel_failures_honor_warn_only(self):
        with hide('everything'):
            host1 = '127.0.0.1:2200'
            host2 = '127.0.0.1:2201'

            @parallel
            def mytask():
                run("ls /")
                if env.host_string == host2:
                    raise OhNoesException

            with settings(warn_only=True):
                result = execute(mytask, hosts=[host1, host2])
            eq_(result[host1], None)
            assert isinstance(result[host2], OhNoesException)
