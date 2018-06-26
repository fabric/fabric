from socket import gaierror

from fabric import ThreadingGroup as Group
from fabric.exceptions import GroupException


class Group_:
    def simple_command(self):
        group = Group("localhost", "127.0.0.1")
        result = group.run("echo foo", hide=True)
        outs = [x.stdout.strip() for x in result.values()]
        assert ["foo", "foo"] == outs

    def failed_command(self):
        group = Group("localhost", "127.0.0.1")
        try:
            group.run("lolnope", hide=True)
        except GroupException as e:
            # GroupException.result -> GroupResult;
            # GroupResult values will be UnexpectedExit in this case;
            # UnexpectedExit.result -> Result, and thus .exited etc.
            exits = [x.result.exited for x in e.result.values()]
            assert [127, 127] == exits
        else:
            assert False, "Did not raise GroupException!"

    def excepted_command(self):
        group = Group("nopebadhost1", "nopebadhost2")
        try:
            group.run("lolnope", hide=True)
        except GroupException as e:
            for value in e.result.values():
                assert isinstance(value, gaierror)
        else:
            assert False, "Did not raise GroupException!"
