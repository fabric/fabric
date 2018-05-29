import os

from invoke import pty_size
from pytest import skip

from fabric import Connection, Config


# TODO: use pytest markers
def skip_outside_travis():
    if not os.environ.get("TRAVIS", False):
        skip()


class Connection_:

    class ssh_connections:

        def open_method_generates_real_connection(self):
            c = Connection("localhost")
            c.open()
            assert c.client.get_transport().active is True
            assert c.is_connected is True
            return c

        def close_method_closes_connection(self):
            # Handy shortcut - open things up, then return Connection for us to
            # close
            c = self.open_method_generates_real_connection()
            c.close()
            assert c.client.get_transport() is None
            assert c.is_connected is False

    class run:

        def simple_command_on_host(self):
            """
            Run command on localhost
            """
            result = Connection("localhost").run("echo foo", hide=True)
            assert result.stdout == "foo\n"
            assert result.exited == 0
            assert result.ok is True

        def simple_command_with_pty(self):
            """
            Run command under PTY on localhost
            """
            # Most Unix systems should have stty, which asplodes when not run
            # under a pty, and prints useful info otherwise
            result = Connection("localhost").run(
                "stty size", hide=True, pty=True
            )
            found = result.stdout.strip().split()
            cols, rows = pty_size()
            assert tuple(map(int, found)), rows == cols
            # PTYs use \r\n, not \n, line separation
            assert "\r\n" in result.stdout
            assert result.pty is True

    class local:

        def wraps_invoke_run(self):
            # NOTE: most of the interesting tests about this are in
            # invoke.runners / invoke.integration.
            cxn = Connection("localhost")
            result = cxn.local("echo foo", hide=True)
            assert result.stdout == "foo\n"
            assert not cxn.is_connected  # meh way of proving it didn't use SSH

    def mixed_use_of_local_and_run(self):
        """
        Run command truly locally, and over SSH via localhost
        """
        cxn = Connection("localhost")
        result = cxn.local("echo foo", hide=True)
        assert result.stdout == "foo\n"
        assert not cxn.is_connected  # meh way of proving it didn't use SSH yet
        result = cxn.run("echo foo", hide=True)
        assert cxn.is_connected  # NOW it's using SSH
        assert result.stdout == "foo\n"

    class sudo:

        def setup(self):
            # NOTE: assumes a user configured for passworded (NOT
            # passwordless)_sudo, whose password is 'mypass', is executing the
            # test suite. I.e. our travis-ci setup.
            config = Config(
                {"sudo": {"password": "mypass"}, "run": {"hide": True}}
            )
            self.cxn = Connection("localhost", config=config)

        def sudo_command(self):
            """
            Run command via sudo on host localhost
            """
            skip_outside_travis()
            assert self.cxn.sudo("whoami").stdout.strip() == "root"

        def mixed_sudo_and_normal_commands(self):
            """
            Run command via sudo, and not via sudo, on localhost
            """
            skip_outside_travis()
            logname = os.environ["LOGNAME"]
            assert self.cxn.run("whoami").stdout.strip() == logname
            assert self.cxn.sudo("whoami").stdout.strip() == "root"

    def large_remote_commands_finish_cleanly(self):
        # Guards against e.g. cleanup finishing before actually reading all
        # data from the remote end. Which is largely an issue in Invoke-level
        # code but one that only really manifests when doing stuff over the
        # network. Yay computers!
        path = "/usr/share/dict/words"
        cxn = Connection("localhost")
        with open(path) as fd:
            words = [x.strip() for x in fd.readlines()]
        stdout = cxn.run("cat {}".format(path), hide=True).stdout
        lines = [x.strip() for x in stdout.splitlines()]
        # When bug present, # lines received is significantly fewer than the
        # true count in the file (by thousands).
        assert len(lines) == len(words)
