from __future__ import with_statement

from StringIO import StringIO

from fabric.api import run, path, put

from util import Integration


class TestOperations(Integration):
    def test_no_trailing_space_in_shell_path_in_run(self):
        run("mkdir -p /tmp/whatever/bin")
        put(StringIO("#!/bin/bash\necho hi"), "/tmp/whatever/bin/myapp", mode="0755")
        with path('/tmp/whatever/bin'):
            assert run('myapp').stdout == 'hi'

    def test_string_put_mode_arg_doesnt_error(self):
        put(StringIO("#!/bin/bash\necho hi"), "/tmp/whocares", mode="0755")
