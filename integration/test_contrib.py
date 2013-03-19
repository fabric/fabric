import types

from fabric.api import env
from fabric.contrib import files


class Integration(object):
    def setup(self):
        env.host_string = "localhost"


def tildify(path):
    home = run("echo ~", quiet=True).stdout.strip()
    return path.replace('~', home)

def expect(path):
    assert files.exists(tildify(path))

def expect_contains(path, value):
    assert files.contains(tildify(path), value)


class TestTildeExpansion(object):
    def test_append(self):
        for target in ('~/append_test', '~/append_test with spaces'):
            files.append(target, ['line'])
            expect(target)

    def test_exists(self):
        for target in ('~/exists_test', '~/exists test with space'):
            run("touch %s" % target)
            expect(target)
     
    def test_sed(self):
        for target in ('~/sed_test', '~/sed test with space'):
            run("echo 'before' > %s" % target)
            files.sed(target, 'before', 'after')
            expect_contains(target, 'after')
     
    def test_upload_template(self):
        for target in ('~/upload_template_test', '~/upload template test with space'):
            files.upload_template(target, target)
            expect(target)
