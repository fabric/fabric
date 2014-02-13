import os
import types
import re
import sys
import shutil
import functools
import signal
import time

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

def expect_has_line(needle, haystack):
    assert re.search(r'^%s$' % needle, haystack, re.M),\
        "'%s' was found in '%s'" % (needle, haystack)

def expect_has_no_line(needle, haystack):
    assert not re.search(r'^%s$' % needle, haystack, re.M),\
        "'%s' was not found in '%s'" % (needle, haystack)


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


def rsync_config(module_name):
    """
    Rsync config decorator

    Generates rsync's config with a named module
    and cleans it up on finish
    """
    def outer(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            pid_file = '/tmp/%s.pid' % module_name
            target_dir = '/tmp/%s' % module_name
            rsync_config = tildify('~/rsyncd.conf')
            # safety measure, maybe the user already has a local config
            if os.path.exists(rsync_config):
                assert False, '%s exists, remove it first' % rsync_config
            # target dir must exist, rsync doesnt create it
            os.mkdir(target_dir)
            with open(rsync_config, 'w') as f:
                f.write(
                    'pid file=%s\n[%s]\npath=%s\nuse chroot=no\n'
                    'read only=no\n' % (pid_file, module_name, target_dir)
                )
            try:
                return fn(
                    *args, module_name=module_name,
                    rsync_opts={
                        'pid_file': pid_file,
                        'config_file': rsync_config
                    }
                )
            finally:
                for path in (rsync_config, pid_file):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                shutil.rmtree(target_dir)
        return inner
    return outer


def rsyncd_server(port):
    """
    Starts rsync server and shuts it down
    on finish
    """
    def read_pid(path):
        try:
            with open(path, 'r') as f:
                try:
                    return int(f.read())
                except ValueError:
                    pass
        except IOError:
            pass

    def is_alive(path):
        tries = 3
        while tries:
            pid = read_pid(path)
            if pid:
                try:
                    os.kill(pid, 0)
                except OSError:
                    pass
                else:
                    break
            tries -= 1
            time.sleep(0.1)
        else:
            return False
        return True

    def kill_proc(path):
        pid = read_pid(path)
        if pid:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    def outer(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            rsync_opts = kwargs['rsync_opts']
            if is_alive(rsync_opts['pid_file']):
                assert False, 'Rsyncd is alive, kill it first'
            rsync_cmd = '/usr/bin/rsync --daemon --port=%s --config=%s'
            local(rsync_cmd % (port, rsync_opts['config_file']))
            if not is_alive(rsync_opts['pid_file']):
                assert False, 'Rsyncd daemon doesnt start'
            rsync_opts.update(port=port)
            try:
                return fn(*args, **kwargs)
            finally:
                kill_proc(rsync_opts['pid_file'])
        return inner
    return outer


rsync_sources = (
    'integration/',
    'integration/test_contrib.py',
    'integration/test_operations.py',
    'integration/utils.py'
)


class TestRsync(Integration):

    def rsync(self, remote_dir, **kwargs):
        opts = dict(
            local_dir='integration',
            capture=True,
            remote_dir=remote_dir,
            **kwargs
        )
        if kwargs.get('transport', 'ssh') == 'ssh':
            opts.update(ssh_opts='-o StrictHostKeyChecking=no')

        try:
            ret = project.rsync_project(**opts)
        finally:
            if (not remote_dir.startswith('::')
                    and os.path.exists(remote_dir)):
                shutil.rmtree(remote_dir)
        return ret

    def test_existing_default_args(self):
        """
        Rsync uses -v by default
        """
        r = self.rsync(remote_dir='/tmp/rsync-test-1')
        for x in rsync_sources:
            expect_has_line(x, r.stdout)

    def test_overriding_default_args(self):
        """
        Use of default_args kwarg can be used to nuke e.g. -v
        """
        r = self.rsync(remote_dir='/tmp/rsync-test-2', default_opts='-pthrz')
        for x in rsync_sources:
            expect_has_no_line(x, r.stdout)

    @rsync_config('rsync-module-test-1')
    def test_named_modules(self, module_name, rsync_opts):
        """
        Use of rsync named modules over ssh

        See man rsync, "USING RSYNC-DAEMON FEATURES VIA A REMOTE-SHELL CONNECTION"
        """
        r = self.rsync(remote_dir='::' + module_name)
        for x in rsync_sources:
            expect_has_line(x, r.stdout)

    @rsync_config('rsync-module-test-2')
    @rsyncd_server(port=8888)
    def test_named_modules_native_protocol(self, module_name, rsync_opts):
        """
        Use of rsync named modules over native protocol

        See man rsync, "CONNECTING TO AN RSYNC DAEMON"
        """
        r = self.rsync(
            remote_dir='::' + module_name,
            extra_opts='--port %s' % rsync_opts['port'],
            transport='native'
        )
        for x in rsync_sources:
            expect_has_line(x, r.stdout)
