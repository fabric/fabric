import types

from fabric.api import env, run, local
from fabric.contrib import files


class Integration(object):
    def setup(self):
        env.host_string = "127.0.0.1"


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
            files.upload_template(src, target)
            expect(target)
