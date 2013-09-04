import os
import types
import sys

from fabric.api import run, local
from fabric.contrib import files, project

from utils import Integration

# Pull in regular tests' stream mocker.
mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tests'))
sys.path.insert(0, mod)
from mock_streams import mock_streams
del sys.path[0]


def tildify(path):
    home = run("echo ~", quiet=True).stdout.strip()
    return path.replace('~', home)

def expect(path):
    assert files.exists(tildify(path))

def expect_contains(path, value):
    assert files.contains(tildify(path), value)

def escape(path):
    return path.replace(' ', r'\ ')


class TestTildeExpansion(Integration):
    def setup(self):
        self.created = []

    def teardown(self):
        super(TestTildeExpansion, self).teardown()
        for created in self.created:
            os.unlink(created)

    def test_append(self):
        for target in ('~/append_test', '~/append_test with spaces'):
            files.append(target, ['line'])
            expect(target)

    def test_exists(self):
        for target in ('~/exists_test', '~/exists test with space'):
            run("touch %s" % escape(target))
            expect(target)
     
    def test_sed(self):
        for target in ('~/sed_test', '~/sed test with space'):
            run("echo 'before' > %s" % escape(target))
            files.sed(target, 'before', 'after')
            expect_contains(target, 'after')
     
    def test_upload_template(self):
        for i, target in enumerate((
            '~/upload_template_test',
            '~/upload template test with space'
        )):
            src = "source%s" % i
            local("touch %s" % src)
            self.created.append(src)
            files.upload_template(src, target)
            expect(target)


class TestIsLink(Integration):
    # TODO: add more of these. meh.
    def test_is_link_is_true_on_symlink(self):
        run("ln -s /tmp/foo /tmp/bar")
        assert files.is_link('/tmp/bar')

    def test_is_link_is_false_on_non_link(self):
        run("touch /tmp/biz")
        assert not files.is_link('/tmp/biz')


class TestRsync(Integration):
    def test_existing_default_args(self):
        # Is verbose by default
        # import mock_streams (sys.path shit I guess)
        # rsync_project(some junk)
        # assert stdout got file list
        pass

    def test_overriding_default_args(self):
        # Lets you remove verbosity
        # import mock_streams (sys.path shit I guess)
        # rsync_project(some junk, default_opts=not-v)
        # assert stdout did not get file list
        pass
