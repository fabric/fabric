import os

from spec import skip, Spec, ok_, eq_
from invoke import pty_size

from fabric import Connection


def skip_outside_travis():
    if not os.environ.get('TRAVIS', False):
        skip()


class Connection_(Spec):
    class ssh_connections:
        def open_method_generates_real_connection(self):
            c = Connection('localhost')
            c.open()
            eq_(c.client.get_transport().active, True)
            eq_(c.is_connected, True)
            return c

        def close_method_closes_connection(self):
            # Handy shortcut - open things up, then return Connection for us to
            # close
            c = self.open_method_generates_real_connection()
            c.close()
            eq_(c.client.get_transport(), None)
            eq_(c.is_connected, False)

    class run:
        def simple_command_on_host(self):
            """
            Run command on localhost
            """
            result = Connection('localhost').run('echo foo', hide=True)
            eq_(result.stdout, "foo\n")
            eq_(result.exited, 0)
            eq_(result.ok, True)

        def simple_command_with_pty(self):
            """
            Run command under PTY on localhost
            """
            # Most Unix systems should have stty, which asplodes when not run
            # under a pty, and prints useful info otherwise
            result = Connection('localhost').run(
                'stty -a', hide=True, pty=True,
            )
            cols, rows = pty_size()
            ok_("{0} rows; {1} columns;".format(rows, cols) in result.stdout)
            # PTYs use \r\n, not \n, line separation
            ok_("\r\n" in result.stdout)
            eq_(result.pty, True)

    class local:
        def wraps_invoke_run(self):
            # NOTE: most of the interesting tests about this are in
            # invoke.runners / invoke.integration.
            cxn = Connection('localhost')
            result = cxn.local('echo foo', hide=True)
            eq_(result.stdout, 'foo\n')
            assert not cxn.is_connected # meh way of proving it didn't use SSH

    def mixed_use_of_local_and_run(self):
        """
        Run command truly locally, and over SSH via localhost
        """
        cxn = Connection('localhost')
        result = cxn.local('echo foo', hide=True)
        eq_(result.stdout, 'foo\n')
        assert not cxn.is_connected # meh way of proving it didn't use SSH yet
        result = cxn.run('echo foo', hide=True)
        assert cxn.is_connected # NOW it's using SSH
        eq_(result.stdout, 'foo\n')

    class sudo:
        def sudo_command(self):
            """
            Run command via sudo on host localhost
            """
            skip_outside_travis()
            eq_(
                Connection('localhost').sudo('whoami').stdout,
                'root\n',
            )

        def mixed_sudo_and_normal_commands(self):
            """
            Run command via sudo, and not via sudo, on localhost
            """
            skip_outside_travis()
            cxn = Connection('localhost')
            cxn.run('whoami')
            cxn.sudo('whoami')
            # Alternately...
            cxn.run('whoami', runner=Basic) # noqa
            cxn.run('whoami', runner=Sudo) # noqa

    def large_remote_commands_finish_cleanly(self):
        # Guards against e.g. cleanup finishing before actually reading all
        # data from the remote end. Which is largely an issue in Invoke-level
        # code but one that only really manifests when doing stuff over the
        # network. Yay computers!
        path = '/usr/share/dict/words'
        cxn = Connection('localhost')
        with open(path) as fd:
            words = [x.strip() for x in fd.readlines()]
        stdout = cxn.run('cat {}'.format(path), hide=True).stdout
        lines = [x.strip() for x in stdout.splitlines()]
        # When bug present, tail of observed stdout != tail of real file
        eq_(lines[-1], words[-1])
        # When bug present, # lines received is significantly fewer than the
        # true count in the file (by thousands).
        eq_(len(lines), len(words))
