import os
import types
import re
import sys

from fabric.api import run, local
from fabric.contrib import files, project

from utils import Integration


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


rsync_sources = (
    'integration/',
    'integration/test_contrib.py',
    'integration/test_operations.py',
    'integration/utils.py'
)

class TestRsync(Integration):
    def rsync(self, id_, **kwargs):
        return project.rsync_project(
            remote_dir='/tmp/rsync-test-%s/' % id_,
            local_dir='integration',
            ssh_opts='-o StrictHostKeyChecking=no',
            capture=True,
            **kwargs
        )

    def test_existing_default_args(self):
        """
        Rsync uses -v by default
        """
        r = self.rsync(1)
        for x in rsync_sources:
            assert re.search(r'^%s$' % x, r.stdout, re.M), "'%s' was not found in '%s'" % (x, r.stdout)

    def test_overriding_default_args(self):
        """
        Use of default_args kwarg can be used to nuke e.g. -v
        """
        r = self.rsync(2, default_opts='-pthrz')
        for x in rsync_sources:
            assert not re.search(r'^%s$' % x, r.stdout, re.M), "'%s' was found in '%s'" % (x, r.stdout)
