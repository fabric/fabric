from __future__ import with_statement

from StringIO import StringIO

from fabric.api import run, path, put

from util import Integration


def assert_mode(path, mode):
    assert run("stat -c \"%%a\" %s" % path).stdout == mode


class TestOperations(Integration):
    filepath = "/tmp/whocares"
    dirpath = "/tmp/whatever/bin"

    def setup(self):
        super(TestOperations, self).setup()
        # Nuke to prevent bleed
        run("rm -rf %s %s" % (self.dirpath, self.filepath))
        # Setup just for kicks
        run("mkdir -p %s" % self.dirpath)

    def test_no_trailing_space_in_shell_path_in_run(self):
        put(StringIO("#!/bin/bash\necho hi"), "%s/myapp" % self.dirpath, mode="0755")
        with path(self.dirpath):
            assert run('myapp').stdout == 'hi'

    def test_string_put_mode_arg_doesnt_error(self):
        put(StringIO("#!/bin/bash\necho hi"), self.filepath, mode="0755")
        assert_mode(self.filepath, "755")

    def test_int_put_mode_works_ok_too(self):
        put(StringIO("#!/bin/bash\necho hi"), self.filepath, mode=0755)
        assert_mode(self.filepath, "755")
