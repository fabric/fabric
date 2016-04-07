from __future__ import with_statement

import hashlib
import os
import posixpath
import stat
import re
from fnmatch import filter as fnfilter

from fabric.state import output, connections, env
from fabric.utils import warn
from fabric.context_managers import settings


# TODO: use self.sftp.listdir_iter on Paramiko 1.15+


def _format_local(local_path, local_is_path):
    """Format a path for log output"""
    if local_is_path:
        return local_path
    else:
        # This allows users to set a name attr on their StringIO objects
        # just like an open file object would have
        return getattr(local_path, 'name', '<file obj>')


class SFTP(object):
    """
    SFTP helper class, which is also a facade for ssh.SFTPClient.
    """
    def __init__(self, host_string):
        self.ftp = connections[host_string].open_sftp()

    # Recall that __getattr__ is the "fallback" attribute getter, and is thus
    # pretty safe to use for facade-like behavior as we're doing here.
    def __getattr__(self, attr):
        return getattr(self.ftp, attr)

    def isdir(self, path):
        try:
            return stat.S_ISDIR(self.ftp.stat(path).st_mode)
        except IOError:
            return False

    def islink(self, path):
        try:
            return stat.S_ISLNK(self.ftp.lstat(path).st_mode)
        except IOError:
            return False

    def exists(self, path):
        try:
            self.ftp.lstat(path).st_mode
        except IOError:
            return False
        return True

    def glob(self, path):
        from fabric.state import win32
        dirpart, pattern = os.path.split(path)
        rlist = self.ftp.listdir(dirpart)

        names = fnfilter([f for f in rlist if not f[0] == '.'], pattern)
        ret = [path]
        if len(names):
            s = '/'
            ret = [dirpart.rstrip(s) + s + name.lstrip(s) for name in names]
            if not win32:
                ret = [posixpath.join(dirpart, name) for name in names]
        return ret

    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        from os.path import join

        # We may not have read permission for top, in which case we can't get a
        # list of the files the directory contains. os.path.walk always
        # suppressed the exception then, rather than blow up for a minor reason
        # when (say) a thousand readable directories are still left to visit.
        # That logic is copied here.
        try:
            # Note that listdir and error are globals in this module due to
            # earlier import-*.
            names = self.ftp.listdir(top)
        except Exception, err:
            if onerror is not None:
                onerror(err)
            return

        dirs, nondirs = [], []
        for name in names:
            if self.isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield top, dirs, nondirs

        for name in dirs:
            path = join(top, name)
            if followlinks or not self.islink(path):
                for x in self.walk(path, topdown, onerror, followlinks):
                    yield x
        if not topdown:
            yield top, dirs, nondirs

    def mkdir(self, path, use_sudo):
        from fabric.api import sudo, hide
        if use_sudo:
            with hide('everything'):
                sudo('mkdir "%s"' % path)
        else:
            self.ftp.mkdir(path)

    def get(self, remote_path, local_path, use_sudo, local_is_path, rremote=None, temp_dir=""):
        from fabric.api import sudo, hide

        # rremote => relative remote path, so get(/var/log) would result in
        # this function being called with
        # remote_path=/var/log/apache2/access.log and
        # rremote=apache2/access.log
        rremote = rremote if rremote is not None else remote_path
        # Handle format string interpolation (e.g. %(dirname)s)
        path_vars = {
            'host': env.host_string.replace(':', '-'),
            'basename': os.path.basename(rremote),
            'dirname': os.path.dirname(rremote),
            'path': rremote
        }

        if local_is_path:
            # Fix for issue #711 and #1348 - escape %'s as well as possible.
            format_re = r'(%%(?!\((?:%s)\)\w))' % '|'.join(path_vars.keys())
            escaped_path = re.sub(format_re, r'%\1', local_path)
            local_path = os.path.abspath(escaped_path % path_vars)

            # Ensure we give ssh.SFTPCLient a file by prepending and/or
            # creating local directories as appropriate.
            dirpath, filepath = os.path.split(local_path)
            if dirpath and not os.path.exists(dirpath):
                os.makedirs(dirpath)
            if os.path.isdir(local_path):
                local_path = os.path.join(local_path, path_vars['basename'])

        if output.running:
            print("[%s] download: %s <- %s" % (
                env.host_string,
                _format_local(local_path, local_is_path),
                remote_path
            ))
        # Warn about overwrites, but keep going
        if local_is_path and os.path.exists(local_path):
            msg = "Local file %s already exists and is being overwritten."
            warn(msg % local_path)

        # When using sudo, "bounce" the file through a guaranteed-unique file
        # path in the default remote CWD (which, typically, the login user will
        # have write permissions on) in order to sudo(cp) it.
        if use_sudo:
            target_path = remote_path
            hasher = hashlib.sha1()
            hasher.update(env.host_string)
            hasher.update(target_path)
            target_path = posixpath.join(temp_dir, hasher.hexdigest())
            # Temporarily nuke 'cwd' so sudo() doesn't "cd" its mv command.
            # (The target path has already been cwd-ified elsewhere.)
            with settings(hide('everything'), cwd=""):
                sudo('cp -p "%s" "%s"' % (remote_path, target_path))
                # The user should always own the copied file.
                sudo('chown %s "%s"' % (env.user, target_path))
                # Only root and the user has the right to read the file
                sudo('chmod %o "%s"' % (0400, target_path))
                remote_path = target_path

        try:
            # File-like objects: reset to file seek 0 (to ensure full overwrite)
            # and then use Paramiko's getfo() directly
            getter = self.ftp.get
            if not local_is_path:
                local_path.seek(0)
                getter = self.ftp.getfo
            getter(remote_path, local_path)
        finally:
            # try to remove the temporary file after the download
            if use_sudo:
                with settings(hide('everything'), cwd=""):
                    sudo('rm -f "%s"' % remote_path)

        # Return local_path object for posterity. (If mutated, caller will want
        # to know.)
        return local_path

    def get_dir(self, remote_path, local_path, use_sudo, temp_dir):
        # Decide what needs to be stripped from remote paths so they're all
        # relative to the given remote_path
        if os.path.basename(remote_path):
            strip = os.path.dirname(remote_path)
        else:
            strip = os.path.dirname(os.path.dirname(remote_path))

        # Store all paths gotten so we can return them when done
        result = []
        # Use our facsimile of os.walk to find all files within remote_path
        for context, dirs, files in self.walk(remote_path):
            # Normalize current directory to be relative
            # E.g. remote_path of /var/log and current dir of /var/log/apache2
            # would be turned into just 'apache2'
            lcontext = rcontext = context.replace(strip, '', 1).lstrip('/')
            # Prepend local path to that to arrive at the local mirrored
            # version of this directory. So if local_path was 'mylogs', we'd
            # end up with 'mylogs/apache2'
            lcontext = os.path.join(local_path, lcontext)

            # Download any files in current directory
            for f in files:
                # Construct full and relative remote paths to this file
                rpath = posixpath.join(context, f)
                rremote = posixpath.join(rcontext, f)
                # If local_path isn't using a format string that expands to
                # include its remote path, we need to add it here.
                if "%(path)s" not in local_path \
                    and "%(dirname)s" not in local_path:
                    lpath = os.path.join(lcontext, f)
                # Otherwise, just passthrough local_path to self.get()
                else:
                    lpath = local_path
                # Now we can make a call to self.get() with specific file paths
                # on both ends.
                result.append(self.get(rpath, lpath, use_sudo, True, rremote, temp_dir))
        return result

    def put(self, local_path, remote_path, use_sudo, mirror_local_mode, mode,
        local_is_path, temp_dir):

        from fabric.api import sudo, hide
        pre = self.ftp.getcwd()
        pre = pre if pre else ''
        if local_is_path and self.isdir(remote_path):
            basename = os.path.basename(local_path)
            remote_path = posixpath.join(remote_path, basename)
        if output.running:
            print("[%s] put: %s -> %s" % (
                env.host_string,
                _format_local(local_path, local_is_path),
                posixpath.join(pre, remote_path)
            ))
        # When using sudo, "bounce" the file through a guaranteed-unique file
        # path in the default remote CWD (which, typically, the login user will
        # have write permissions on) in order to sudo(mv) it later.
        if use_sudo:
            target_path = remote_path
            hasher = hashlib.sha1()
            hasher.update(env.host_string)
            hasher.update(target_path)
            remote_path = posixpath.join(temp_dir, hasher.hexdigest())
        # Read, ensuring we handle file-like objects correct re: seek pointer
        putter = self.ftp.put
        if not local_is_path:
            old_pointer = local_path.tell()
            local_path.seek(0)
            putter = self.ftp.putfo
        rattrs = putter(local_path, remote_path)
        if not local_is_path:
            local_path.seek(old_pointer)
        # Handle modes if necessary
        if (local_is_path and mirror_local_mode) or (mode is not None):
            lmode = os.stat(local_path).st_mode if mirror_local_mode else mode
            # Cast to octal integer in case of string
            if isinstance(lmode, basestring):
                lmode = int(lmode, 8)
            lmode = lmode & 07777
            rmode = rattrs.st_mode
            # Only bitshift if we actually got an rmode
            if rmode is not None:
                rmode = (rmode & 07777)
            if lmode != rmode:
                if use_sudo:
                    # Temporarily nuke 'cwd' so sudo() doesn't "cd" its mv
                    # command. (The target path has already been cwd-ified
                    # elsewhere.)
                    with settings(hide('everything'), cwd=""):
                        sudo('chmod %o \"%s\"' % (lmode, remote_path))
                else:
                    self.ftp.chmod(remote_path, lmode)
        if use_sudo:
            # Temporarily nuke 'cwd' so sudo() doesn't "cd" its mv command.
            # (The target path has already been cwd-ified elsewhere.)
            with settings(hide('everything'), cwd=""):
                sudo("mv \"%s\" \"%s\"" % (remote_path, target_path))
            # Revert to original remote_path for return value's sake
            remote_path = target_path
        return remote_path

    def put_dir(self, local_path, remote_path, use_sudo, mirror_local_mode,
        mode, temp_dir):
        if os.path.basename(local_path):
            strip = os.path.dirname(local_path)
        else:
            strip = os.path.dirname(os.path.dirname(local_path))

        remote_paths = []

        for context, dirs, files in os.walk(local_path):
            rcontext = context.replace(strip, '', 1)
            # normalize pathname separators with POSIX separator
            rcontext = rcontext.replace(os.sep, '/')
            rcontext = rcontext.lstrip('/')
            rcontext = posixpath.join(remote_path, rcontext)

            if not self.exists(rcontext):
                self.mkdir(rcontext, use_sudo)

            for d in dirs:
                n = posixpath.join(rcontext, d)
                if not self.exists(n):
                    self.mkdir(n, use_sudo)

            for f in files:
                local_path = os.path.join(context, f)
                n = posixpath.join(rcontext, f)
                p = self.put(local_path, n, use_sudo, mirror_local_mode, mode,
                    True, temp_dir)
                remote_paths.append(p)
        return remote_paths
