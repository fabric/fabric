import os
import types

from fabric.api import run, local
from fabric.contrib import files

from util import Integration


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
