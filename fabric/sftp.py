import stat
import os
from fnmatch import filter as fnfilter

from fabric.state import output, connections, env
from fabric.utils import warn


class SFTP(object):
    """
    SFTP helper class, which is also a facade for paramiko.SFTPClient.
    """
    def __init__(self, host_string):
        self.ftp = connections[host_string].open_sftp()


    # Recall that __getattr__ is the "fallback" attribute getter, and is thus
    # pretty safe to use for facade-like behavior as we're doing here.
    def __getattr__(self, attr):
        return getattr(self.ftp, attr)


    def isdir(self, path):
        try:
            return stat.S_ISDIR(self.ftp.lstat(path).st_mode)
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
        dirpart, pattern = os.path.split(path)
        rlist = self.ftp.listdir(dirpart)

        names = fnfilter([f for f in rlist if not f[0] == '.'], pattern)
        if len(names):
            return [os.path.join(dirpart, name) for name in names]
        else:
            return [path]


    def walk(self, top, topdown=True, onerror=None, followlinks=False):
        from os.path import join, isdir, islink

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

    def get(self, remote_path, local_path):
        if os.path.isdir(local_path):
            local_path = os.path.join(local_path, os.path.basename(remote_path))
        if output.running:
            print("[%s] download: %s <- %s" % (
                env.host_string, local_path, remote_path
            ))
        if os.path.exists(local_path):
            msg = "Local file %s already exists and is being overwritten."
            warn(msg % local_path)
        # Handle any raised exceptions (no return code to inspect here)
        self.ftp.get(remote_path, local_path)


    def get_dir(self, remote_path, local_path):
        if os.path.basename(remote_path):
            strip = os.path.dirname(remote_path)
        else:
            strip = os.path.dirname(os.path.dirname(remote_path))

        for context, dirs, files in self.walk(remote_path):
            lcontext = context.replace(strip,'')
            lcontext = lcontext.lstrip('/')
            lcontext = os.path.join(local_path, lcontext)

            if not os.path.exists(lcontext):
                os.mkdir(lcontext)
            for d in dirs:
                n = os.path.join(lcontext, d)
                if not os.path.exists(n):
                    os.mkdir(n)
            for f in files:
                remote_path = os.path.join(context, f)
                n = os.path.join(lcontext, f)
                self.get(remote_path, n)

    def put(self, local_path, remote_path):
        pre = self.ftp.getcwd()
        pre = pre if pre else ''

        if self.isdir(remote_path):
            basename = os.path.basename(local_path)
            remote_path = os.path.join(remote_path, basename)
        if output.running:
            print("[%s] put: %s -> %s" % (
                env.host_string, local_path, os.path.join(pre, remote_path)
            ))
        # Try to catch raised exceptions (which is the only way to tell if
        # this operation had problems; there's no return code) during upload
        # Actually do the upload
        rattrs = self.ftp.put(local_path, remote_path)
        # and finally set the file mode
        lmode = os.stat(local_path).st_mode
        if lmode != rattrs.st_mode:
            self.ftp.chmod(remote_path, lmode)

    def put_dir(self, local_path, remote_path):
        if os.path.basename(local_path):
            strip = os.path.dirname(local_path)
        else:
            strip = os.path.dirname(os.path.dirname(local_path))

        for context, dirs, files in os.walk(local_path):
            rcontext = context.replace(strip,'')
            rcontext = rcontext.lstrip('/')
            rcontext = os.path.join(remote_path, rcontext)

            if not self.exists(rcontext):
                self.ftp.mkdir(rcontext)

            for d in dirs:
                n = os.path.join(rcontext,d)
                if not self.exists(n):
                    self.ftp.mkdir(n)

            for f in files:
                local_path = os.path.join(context,f)
                n = os.path.join(rcontext,f)
                self.put(local_path, n)
