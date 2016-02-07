from fabric.context_managers import hide, settings
from fabric.decorators import parallel
from fabric.operations import run
from fabric.state import env
from fabric.tasks import execute

from utils import FabricTest, eq_, aborts
from mock_streams import mock_streams
from server import server, RESPONSES, USER, HOST, PORT

# TODO: move this into test_tasks? meh.

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
    def test_env_host_no_user_or_port(self):
        """
        Ensure env.host doesn't get user/port parts when parallel
        """
        @parallel
        def _task():
            run("ls /simple")
            assert USER not in env.host
            assert str(PORT) not in env.host

        host_string = '%s@%s:%%s' % (USER, HOST)
        with hide('everything'):
            execute(_task, hosts=[host_string % 2200, host_string % 2201])

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
    @mock_streams('stderr') # To hide the traceback for now
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


    @server(port=2200)
    @server(port=2201)
    def test_parallel_implies_linewise(self):
        host1 = '127.0.0.1:2200'
        host2 = '127.0.0.1:2201'

        assert not env.linewise

        @parallel
        def mytask():
            run("ls /")
            return env.linewise

        with hide('everything'):
            result = execute(mytask, hosts=[host1, host2])
        eq_(result[host1], True)
        eq_(result[host2], True)
