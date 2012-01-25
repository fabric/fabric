from __future__ import with_statement

import hashlib
import os
import stat
import tempfile
from fnmatch import filter as fnfilter

from fabric.state import output, connections, env
from fabric.utils import warn
from fabric.context_managers import settings


class DryRunSFTP(object):
    """
    SFTP helper class - dry run version that doesn't actually do anything
    _try_ to return something 'sane' for the methods that are used.
    TODO: possibly allow this to be redirected to a local filesystem for more sensible testing?
    """
    def __init__(self, host_string):
        pass

    def normalize(self, path):
        return path
        
    def close(self):
        return

    def isdir(self, path):
        return False

    def islink(self, path):
        return False

    def exists(self, path):
        return False


    def glob(self, path):
        return [path]


    def walk(self, top, topdown=True, onerror=None, followlinks=False):
            return

    def mkdir(self, path, use_sudo):
        return


    def get(self, remote_path, local_path, local_is_path, rremote=None):
        return

    def get_dir(self, remote_path, local_path):
        return

    def put(self, local_path, remote_path, use_sudo, mirror_local_mode, mode,
        local_is_path):
        from fabric.api import sudo, hide
        # TODO: support simulated remote working directory
        # pre = self.ftp.getcwd()
        # pre = pre if pre else ''
        pre = ''
        #  if local_is_path and self.isdir(remote_path):
        #      basename = os.path.basename(local_path)
        #      remote_path = os.path.join(remote_path, basename)

        print("[%s] put: %s -> %s" % (
            env.host_string,
            local_path if local_is_path else '<file obj>',
            os.path.join(pre, remote_path)
        ))
        

    def put_dir(self, local_path, remote_path, use_sudo, mirror_local_mode,
        mode):
        if os.path.basename(local_path):
            strip = os.path.dirname(local_path)
        else:
            strip = os.path.dirname(os.path.dirname(local_path))

        remote_paths = []

        for context, dirs, files in os.walk(local_path):
            rcontext = context.replace(strip, '', 1)
            rcontext = rcontext.lstrip('/')
            rcontext = os.path.join(remote_path, rcontext)

            if not self.exists(rcontext):
                self.mkdir(rcontext, use_sudo)

            for d in dirs:
                n = os.path.join(rcontext, d)
                if not self.exists(n):
                    self.mkdir(n, use_sudo)

            for f in files:
                local_path = os.path.join(context, f)
                n = os.path.join(rcontext, f)
                p = self.put(local_path, n, use_sudo, mirror_local_mode, mode,
                    True)
                remote_paths.append(p)
        return remote_paths
